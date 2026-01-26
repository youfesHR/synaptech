#!/usr/bin/env python3
"""
Data exploration script for HER2-ResistAID project.
Run this to explore the real data you've downloaded.
"""

import sys
import os
sys.path.append('../src')

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from data_loader import HER2DataLoader

def explore_data():
    """Explore the downloaded data"""
    print("🔬 Exploring HER2-ResistAID Data")
    print("=" * 50)
    
    # Initialize loader
    loader = HER2DataLoader()
    
    # Load data
    print("\n1. Loading mutations...")
    mutations = loader.load_cbioportal_mutations(force_download=False)
    
    print("\n2. Loading antibodies...")
    antibodies = loader.load_real_antibodies_from_sabdab()
    
    print("\n3. Loading abstracts...")
    abstracts = loader.load_pubmed_abstracts()
    
    # Display statistics
    print("\n" + "=" * 50)
    print("📊 DATA STATISTICS")
    print("=" * 50)
    
    print(f"\n🧬 Mutations:")
    print(f"   Total records: {len(mutations)}")
    if not mutations.empty:
        print(f"   Columns: {list(mutations.columns)}")
        print(f"   Unique mutations: {mutations['mutation_id'].nunique()}")
        
        # Show top mutations
        if 'mutation_id' in mutations.columns:
            top_mutations = mutations['mutation_id'].value_counts().head(10)
            print(f"\n   Top mutations:")
            for mut, count in top_mutations.items():
                print(f"     {mut}: {count} occurrences")
    
    print(f"\n💉 Antibodies:")
    print(f"   Total sequences: {len(antibodies)}")
    if not antibodies.empty:
        print(f"   Antibody names: {antibodies['name'].tolist()}")
        print(f"   Sources: {antibodies['source'].unique().tolist()}")
    
    print(f"\n📚 Scientific Abstracts:")
    print(f"   Total abstracts: {len(abstracts)}")
    if not abstracts.empty:
        print(f"   Years: {abstracts['year'].unique()}")
        print(f"   Sample title: {abstracts.iloc[0]['title'][:80]}...")
    
    # Save summary report
    summary = {
        'dataset': ['Mutations', 'Antibodies', 'Abstracts'],
        'count': [len(mutations), len(antibodies), len(abstracts)],
        'source': ['cBioPortal', 'SAbDab + Literature', 'PubMed']
    }
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('../data/processed/data_summary.csv', index=False)
    
    print(f"\n📄 Summary saved to: data/processed/data_summary.csv")
    
    # Create simple visualizations
    if not mutations.empty and 'mutation_type' in mutations.columns:
        print("\n📈 Creating visualizations...")
        
        plt.figure(figsize=(10, 6))
        
        # Mutation type distribution
        mutation_types = mutations['mutation_type'].value_counts().head(5)
        plt.subplot(1, 2, 1)
        mutation_types.plot(kind='bar', color='skyblue')
        plt.title('Top 5 Mutation Types')
        plt.xlabel('Mutation Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        
        # Antibody source distribution
        if not antibodies.empty and 'source' in antibodies.columns:
            plt.subplot(1, 2, 2)
            sources = antibodies['source'].value_counts()
            sources.plot(kind='pie', autopct='%1.1f%%', colors=['lightcoral', 'lightgreen', 'lightblue'])
            plt.title('Antibody Sources')
        
        plt.tight_layout()
        plt.savefig('../data/processed/data_distribution.png', dpi=150, bbox_inches='tight')
        print(f"   Visualization saved to: data/processed/data_distribution.png")
    
    print("\n✅ Data exploration complete!")
    
    # Show sample data
    print("\n" + "=" * 50)
    print("🎯 SAMPLE MUTATION DATA")
    print("=" * 50)
    
    if not mutations.empty:
        sample = mutations.head(3)
        for _, row in sample.iterrows():
            print(f"\nMutation: {row.get('mutation_id', 'Unknown')}")
            print(f"  Type: {row.get('mutation_type', 'N/A')}")
            print(f"  AA Change: {row.get('amino_acid_change', 'N/A')}")
            if 'protein_position' in row:
                print(f"  Position: {row.get('protein_position', 'N/A')}")

if __name__ == "__main__":
    explore_data()