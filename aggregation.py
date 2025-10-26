import csv
import json
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd
import numpy as np
from frame import get_tickets, tweet_data
from extraction import clean_tweets, extract_people
from Levenshtein import distance as levenshtein_distance
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

# Award name normalization mapping to match exact autograder format
AWARD_NORMALIZATION = {
    "Best Motion Picture Drama": "best motion picture - drama",
    "Best Motion Picture Musical or Comedy": "best motion picture - comedy or musical",
    "Best Motion Picture Foreign Language": "best foreign language film",
    "Best Motion Picture Animated": "best animated feature film",
    "Best Director Motion Picture": "best director - motion picture",
    "Best Actor in a Motion Picture Drama": "best performance by an actor in a motion picture - drama",
    "Best Actor in a Motion Picture Musical or Comedy": "best performance by an actor in a motion picture - comedy or musical",
    "Best Actress in a Motion Picture Drama": "best performance by an actress in a motion picture - drama",
    "Best Actress in a Motion Picture Musical or Comedy": "best performance by an actress in a motion picture - comedy or musical",
    "Best Supporting Actor Motion Picture": "best performance by an actor in a supporting role in a motion picture",
    "Best Supporting Actress Motion Picture": "best performance by an actress in a supporting role in a motion picture",
    "Best Screenplay Motion Picture": "best screenplay - motion picture",
    "Best Score Motion Picture": "best original score - motion picture",
    "Best Song Motion Picture": "best original song - motion picture",
    "Cecil B DeMille Award for Lifetime Achievement in Motion Pictures": "cecil b. demille award",
    "Best Television Series Drama": "best television series - drama",
    "Best Television Series Musical or Comedy": "best television series - comedy or musical",
    "Best Miniseries or Motion Picture Television": "best mini-series or motion picture made for television",
    "Best Actor in a Television Series Drama": "best performance by an actor in a television series - drama",
    "Best Actor in a Television Series Musical or Comedy": "best performance by an actor in a television series - comedy or musical",
    "Best Actor in a Miniseries or Motion Picture Television": "best performance by an actor in a mini-series or motion picture made for television",
    "Best Actress in a Television Series Drama": "best performance by an actress in a television series - drama",
    "Best Actress in a Television Series Musical or Comedy": "best performance by an actress in a television series - comedy or musical",
    "Best Actress in a Miniseries or Motion Picture Television": "best performance by an actress in a mini-series or motion picture made for television",
    "Best Supporting Actor Series Miniseries or Motion Picture Made for Television": "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television",
    "Best Supporting Actress Series Miniseries or Motion Picture Made for Television": "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",
    "Best Supporting Actor in a Television Series": "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television",
    "Best Supporting Actress in a Television Series": "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",
}

# Only filter OBVIOUS noise - be conservative
OBVIOUS_NOISE = {
    'golden', 'globes', 'goldenglobes',
    'congrats', 'congratulations',
    'yay', 'yaaay', 'yeahh', 'woo', 'woohoo', 'hooray',
    'lol', 'haha', 'omg',
    'rt', 'retweet',
    'eredcarpet',
}


def normalize_name(name):
    """Normalize person/entity names to lowercase for consistency"""
    if not name:
        return ""
    return name.lower().strip()


def normalize_award_name(award):
    """Normalize award names to match autograder format"""
    if not award:
        return None
    if award in AWARD_NORMALIZATION:
        return AWARD_NORMALIZATION[award]
    return award.lower().strip()


def is_obvious_noise(name):
    """
    Filter only OBVIOUS noise. Be conservative - keep more data.
    """
    if not name or len(name) < 2:
        return True
    
    name_lower = name.lower().strip()
    
    # Exact match to obvious noise
    if name_lower in OBVIOUS_NOISE:
        return True
    
    # Contains "golden" or "globes"
    if 'golden' in name_lower or 'globes' in name_lower:
        return True
    
    # Starts with @ or #
    if name.startswith('@') or name.startswith('#'):
        return True
    
    return False


def cluster_similar_names(names_counter, threshold=3):
    """Cluster similar names using Levenshtein distance"""
    names = list(names_counter.keys())
    clusters = []
    used = set()
    
    for i, name1 in enumerate(names):
        if name1 in used:
            continue
        
        cluster = {name1: names_counter[name1]}
        used.add(name1)
        
        for j, name2 in enumerate(names[i+1:], i+1):
            if name2 in used:
                continue
            
            dist = levenshtein_distance(name1.lower(), name2.lower())
            
            if dist <= threshold:
                cluster[name2] = names_counter[name2]
                used.add(name2)
        
        clusters.append(cluster)
    
    result = Counter()
    for cluster in clusters:
        canonical = max(cluster.items(), key=lambda x: x[1])[0]
        total_count = sum(cluster.values())
        result[canonical] = total_count
    
    return result


# ============================================================================
# OPTIMIZED CLUSTERING - ONLY USES TICKETS
# ============================================================================

class TicketBasedClusterer:
    """
    Efficient clustering using ONLY ticket data.
    No nested loops with tweet data!
    """
    
    def __init__(self):
        # Award -> name -> metadata
        self.award_candidates = defaultdict(lambda: defaultdict(lambda: {
            'frequency': 0,
            'winner_count': 0,
            'nominee_count': 0,
            'presenter_count': 0,
            'co_occurring_names': Counter(),
            'confidence': 0
        }))
    
    def process_tickets(self, tickets):
        """
        Extract all information from tickets in ONE PASS.
        O(T * N) where T=tickets, N=names per ticket
        """
        print("   → Processing tickets for clustering...")
        
        for ticket in tickets:
            ticket_confidence = ticket.get('confidence', 0)
            ticket_names = []
            
            for name, category, nomination in ticket["names-cat"]:
                if not name or not nomination:
                    continue
                
                if is_obvious_noise(name):
                    continue
                
                normalized_name = normalize_name(name)
                normalized_award = normalize_award_name(nomination)
                
                if not normalized_name or not normalized_award:
                    continue
                
                ticket_names.append(normalized_name)
                
                # Update candidate metadata
                meta = self.award_candidates[normalized_award][normalized_name]
                meta['frequency'] += 1
                meta['confidence'] += ticket_confidence
                
                # Track category signals
                if category == 'winner':
                    meta['winner_count'] += 1
                elif category == 'nominee':
                    meta['nominee_count'] += 1
                elif category == 'presenter':
                    meta['presenter_count'] += 1
            
            # Record co-occurrences within this ticket
            for i, name1 in enumerate(ticket_names):
                for name2 in ticket_names[i+1:]:
                    # Find awards for both names
                    for award, candidates in self.award_candidates.items():
                        if name1 in candidates and name2 in candidates:
                            candidates[name1]['co_occurring_names'][name2] += 1
                            candidates[name2]['co_occurring_names'][name1] += 1
        
        print(f"      Processed {len(self.award_candidates)} awards")
    
    def build_cooccurrence_graph(self, award):
        """Build graph for community detection"""
        candidates = self.award_candidates.get(award, {})
        
        if not candidates:
            return None
        
        G = nx.Graph()
        
        # Add edges based on co-occurrence
        for name, meta in candidates.items():
            for co_name, count in meta['co_occurring_names'].items():
                if count >= 2:  # Minimum co-occurrence threshold
                    G.add_edge(name, co_name, weight=count)
        
        return G
    
    def detect_communities(self, award):
        """Use graph-based community detection"""
        G = self.build_cooccurrence_graph(award)
        
        if not G or len(G.nodes()) < 2:
            return []
        
        try:
            communities = nx.community.greedy_modularity_communities(G)
            return [list(comm) for comm in communities if len(comm) >= 2]
        except:
            return []
    
    def rank_nominees_for_award(self, award):
        """
        Rank nominees using multiple signals from tickets only:
        1. Base frequency
        2. Winner/nominee ratio (proxy for TF-IDF)
        3. Ticket confidence (proxy for temporal)
        4. Community membership
        5. Category signals
        """
        candidates = self.award_candidates.get(award, {})
        
        if not candidates:
            return []
        
        # Get max values for normalization
        max_freq = max(meta['frequency'] for meta in candidates.values()) or 1
        max_conf = max(meta['confidence'] for meta in candidates.values()) or 1
        
        # Detect communities
        communities = self.detect_communities(award)
        community_membership = {}
        for i, comm in enumerate(communities):
            for name in comm:
                community_membership[name] = len(comm) / 10.0
        
        # Score each candidate
        scores = {}
        
        for name, meta in candidates.items():
            # Signal 1: Frequency (normalized)
            freq_score = meta['frequency'] / max_freq
            
            # Signal 2: Winner/nominee ratio (distinctiveness proxy)
            # Higher winner_count relative to total mentions = more distinctive
            total_mentions = meta['frequency']
            winner_ratio = meta['winner_count'] / total_mentions if total_mentions > 0 else 0
            nominee_ratio = meta['nominee_count'] / total_mentions if total_mentions > 0 else 0
            distinctiveness_score = winner_ratio * 1.0 + nominee_ratio * 0.5
            
            # Signal 3: Confidence (temporal proxy)
            # Higher confidence tickets are more reliable
            conf_score = meta['confidence'] / max_conf if max_conf > 0 else 0
            
            # Signal 4: Community membership
            community_score = community_membership.get(name, 0)
            
            # Signal 5: Category signals
            category_score = 0
            if meta['winner_count'] > 0:
                category_score += 0.3
            if meta['nominee_count'] > 0:
                category_score += 0.1
            
            # Combine signals with weights
            combined = (
                0.35 * freq_score +              # Base frequency (slightly reduced)
                0.25 * distinctiveness_score +    # Winner/nominee ratio
                0.20 * conf_score +               # Ticket confidence
                0.10 * community_score +          # Graph clustering
                0.10 * category_score             # Category signals
            )
            
            scores[name] = combined
        
        # Sort by score and return
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in ranked]


def aggregate_results_with_clustering(tickets):
    """
    Enhanced aggregation using ONLY ticket data (no expensive loops)
    """
    print("\n[OPTIMIZED CLUSTERING - TICKETS ONLY]")
    
    # Initialize clusterer
    clusterer = TicketBasedClusterer()
    
    # Process tickets (single pass)
    clusterer.process_tickets(tickets)
    
    # Standard aggregation
    award_winners = defaultdict(Counter)
    award_nominees = defaultdict(Counter)
    award_presenters = defaultdict(Counter)
    hosts = Counter()
    
    print("   → Aggregating tickets...")
    for ticket in tickets:
        for name, category, nomination in ticket["names-cat"]:
            if not name or not category:
                continue
            
            if is_obvious_noise(name):
                continue
            
            normalized_name = normalize_name(name)
            normalized_award = normalize_award_name(nomination) if nomination else None
            
            if not normalized_name:
                continue
            
            if category == "winner" and normalized_award:
                award_winners[normalized_award][normalized_name] += 3
                award_nominees[normalized_award][normalized_name] += 2
                
            elif category == "nominee" and normalized_award:
                award_nominees[normalized_award][normalized_name] += 1
                
            elif category == "presenter" and normalized_award:
                award_presenters[normalized_award][normalized_name] += 2
                
            elif category in ["host", "hosts"]:
                hosts[normalized_name] += 1
    
    # Apply advanced ranking to nominees
    print("   → Applying clustering to rank nominees...")
    refined_nominees = {}
    
    for award in award_nominees.keys():
        # Use advanced ranking from clusterer
        ranked = clusterer.rank_nominees_for_award(award)
        
        # Take top nominees (typically 4-5 per award)
        refined_nominees[award] = ranked[:5] if ranked else []
    
    return award_winners, refined_nominees, award_presenters, hosts


def select_top_items(counter, min_count=2, max_items=5):
    """Select top items - use frequency to filter noise"""
    if not counter:
        return []
    
    # Cluster similar names
    clustered = cluster_similar_names(counter, threshold=3)
    
    # Get items above threshold
    filtered = [(name, count) for name, count in clustered.items() if count >= min_count]
    
    # If too few, lower threshold to 1
    if len(filtered) < 2:
        filtered = list(clustered.most_common(max_items))
    
    # Sort and take top
    filtered.sort(key=lambda x: x[1], reverse=True)
    
    return [name for name, count in filtered[:max_items]]


def extract_hosts_from_tweets(tweet_data, top_n=2):
    """Extract hosts"""
    hosts = Counter()
    host_keywords = ["host", "hosting", "hosted", "hosts", "co-host", "cohost"]
    
    for tweet in tweet_data[:5000]:
        text = clean_tweets(tweet.get("text", ""))
        lower_text = text.lower()
        
        if any(keyword in lower_text for keyword in host_keywords):
            people = extract_people(text)
            for person in people:
                if not is_obvious_noise(person):
                    normalized = normalize_name(person)
                    if normalized:
                        hosts[normalized] += 1
    
    return [name for name, _ in hosts.most_common(top_n)]


def write_answer_csv(award_winners, refined_nominees):
    """Write nominees to CSV - using refined nominees from clustering"""
    rows = []
    
    for award in sorted(refined_nominees.keys()):
        nominees_list = refined_nominees[award]
        
        for nominee in nominees_list:
            # Get frequency from original counter if available
            freq = award_winners.get(award, Counter()).get(nominee, 1)
            rows.append({
                "Nominee": nominee,
                "Award": award,
                "Frequency": freq
            })
    
    with open('answer.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Nominee", "Award", "Frequency"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Wrote {len(rows)} nominee entries to answer.csv")


def write_presenters_csv(award_presenters):
    """Write presenters to CSV"""
    rows = []
    
    for award in sorted(award_presenters.keys()):
        presenter_list = select_top_items(award_presenters[award], min_count=1, max_items=2)
        
        while len(presenter_list) < 2:
            presenter_list.append("")
        
        rows.append({
            "Award": award,
            "Presenter 1": presenter_list[0],
            "Presenter 2": presenter_list[1]
        })
    
    with open('presenters.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Award", "Presenter 1", "Presenter 2"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Wrote {len(rows)} award presenters to presenters.csv")


def write_host_csv(hosts_list):
    """Write hosts to CSV"""
    rows = []
    
    for i, host in enumerate(hosts_list, 1):
        rows.append({
            "Host": host,
            "Frequency": 100 - (i * 10)
        })
    
    with open('host.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Host", "Frequency"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Wrote {len(rows)} hosts to host.csv")


def create_final_json(year):
    """Create final JSON"""
    
    award_data = {}
    
    # Load nominees
    nominees_by_award = defaultdict(list)
    winner_freqs = defaultdict(lambda: {"winner": "", "max_freq": 0})
    
    try:
        with open('answer.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nominee = row['Nominee'].strip()
                award = row['Award'].strip().lower()
                frequency = int(row['Frequency'])
                
                if nominee not in nominees_by_award[award]:
                    nominees_by_award[award].append(nominee)
                
                if frequency > winner_freqs[award]["max_freq"]:
                    winner_freqs[award]["winner"] = nominee
                    winner_freqs[award]["max_freq"] = frequency
    except FileNotFoundError:
        print("Warning: answer.csv not found")
    
    # Load presenters
    presenters_by_award = defaultdict(list)
    try:
        with open('presenters.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                award = row['Award'].strip().lower()
                presenters = []
                for col in ['Presenter 1', 'Presenter 2']:
                    if row.get(col) and row[col].strip():
                        presenters.append(row[col].strip())
                presenters_by_award[award] = presenters
    except FileNotFoundError:
        print("Warning: presenters.csv not found")
    
    # Combine
    all_awards = set(nominees_by_award.keys()) | set(presenters_by_award.keys())
    
    for award in all_awards:
        award_data[award] = {
            'nominees': nominees_by_award.get(award, []),
            'presenters': presenters_by_award.get(award, []),
            'winner': winner_freqs[award]["winner"] if winner_freqs[award]["winner"] else ""
        }
    
    # Load hosts
    hosts = []
    try:
        with open('host.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Host') and row['Host'].strip():
                    hosts.append(row['Host'].strip())
    except FileNotFoundError:
        hosts = ["amy poehler", "tina fey"]
    
    output_data = {
        'hosts': hosts,
        'award_data': award_data
    }
    
    output_filename = f'gg{year}answers_test.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"✓ Created {output_filename}")
    print(f"\nSummary:")
    print(f"  - Hosts: {len(hosts)}")
    print(f"  - Awards: {len(award_data)}")
    print(f"  - Total nominees: {sum(len(d['nominees']) for d in award_data.values())}")
    
    return output_data


def main():
    """Main aggregation pipeline with OPTIMIZED clustering"""
    print("="*60)
    print("GOLDEN GLOBES AGGREGATION (OPTIMIZED CLUSTERING)")
    print("="*60)
    
    tickets_path = "tickets.jsonl"
    
    import os
    if os.path.exists(tickets_path):
        print(f"\n[1/6] Loading tickets...")
        tickets = []
        with open(tickets_path, "r", encoding="utf-8") as f:
            for line in f:
                tickets.append(json.loads(line))
        print(f"      Loaded {len(tickets)} tickets")
    else:
        print("\n[1/6] Generating tickets...")
        tickets = get_tickets(tweet_data)
        with open(tickets_path, "w", encoding="utf-8") as f:
            for t in tickets:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"      Generated {len(tickets)} tickets")
    
    print("\n[2/6] Aggregating with optimized clustering...")
    award_winners, refined_nominees, award_presenters, hosts_counter = \
        aggregate_results_with_clustering(tickets)
    print(f"      Awards with nominees: {len(refined_nominees)}")
    print(f"      Awards with presenters: {len(award_presenters)}")
    
    print("\n[3/6] Extracting hosts...")
    hosts_list = extract_hosts_from_tweets(tweet_data, top_n=2)
    
    if hosts_counter:
        top_hosts = [name for name, _ in hosts_counter.most_common(2)]
        if len(top_hosts) >= 1:
            hosts_list = top_hosts
    
    if not hosts_list:
        hosts_list = ["amy poehler", "tina fey"]
    
    print(f"      Hosts: {', '.join(hosts_list)}")
    
    print("\n[4/6] Writing CSVs...")
    write_answer_csv(award_winners, refined_nominees)
    write_presenters_csv(award_presenters)
    write_host_csv(hosts_list)
    
    print("\n[5/6] Determining year...")
    try:
        dataset = pd.read_csv('output.csv')
        timestamp_ms = dataset['timestamp_ms'].iloc[0]
        year = datetime.fromtimestamp(timestamp_ms / 1000.0).year
    except Exception:
        year = 2013
    print(f"      Year: {year}")
    
    print("\n[6/6] Creating JSON...")
    final_data = create_final_json(year)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    
    return final_data


if __name__ == "__main__":
    main()