#!/usr/bin/env python3
"""
Test script for NormCode translator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.normcode_translator import NormCodeTranslator

def test_simple_normcode():
    """Test simple NormCode translation"""
    translator = NormCodeTranslator()
    
    # Test simple horizontal layout
    normcode_text = "|1|_inferred_1_ |1.1|<= _primary_functional_1_ |/1.1| |1.2|<- _value_1_ |/1.2| |/1|"
    
    nodes, edges = translator.parse_horizontal_layout(normcode_text)
    
    print("=== Simple NormCode Test ===")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")

def test_complex_normcode():
    """Test complex NormCode with nested structure"""
    translator = NormCodeTranslator()
    
    # Test complex horizontal layout
    normcode_text = """|1|_inferred_1_ |1.1|<= _primary_functional_1_ |1.1.1|<= _primary_functional_2_ |/1.1.1||1.1.2|<- _value_for_2_ |/1.1.2| |/1.1| |1.2|<- _value_3_ |1.2.1|<= _primary_functional_for_3_ |/1.2.1||1.2.2|<- _values_for_3_ |/1.2.2||/1.2||/1|"""
    
    nodes, edges = translator.parse_horizontal_layout(normcode_text)
    
    print("\n=== Complex NormCode Test ===")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")

def test_real_examples():
    """Test with real examples from complete analysis QA pairs"""
    translator = NormCodeTranslator()
    
    print("\n=== Real Examples Test ===")
    
    # Example 1: User account creation process (Objects and Imperatives)
    example1 = "|1|{user_account_creation_process} |1.1|<= $= |1.1.1|<- <To create a user account> |/1.1.1| |1.1.2|<- across(<you must provide a valid email address>, <choose a strong password>) |/1.1.2| |/1.1| |/1|"
    
    print("\n--- Example 1: User Account Creation Process ---")
    nodes, edges = translator.parse_horizontal_layout(example1)
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")
    
    # Example 2: Password requirements (Objects and Judgements)
    example2 = "|1|{password_requirements} |1.1|<= $= |1.1.1|<- <{1}<${ALL TRUE}%_>> |1.1.1.1|&across( |1.1.1.1.1|<{2}<$({length})%_> characters long> |1.1.1.1.2|<{3}<$({character_types})%_>> |/1.1.1.1.2|) |/1.1.1.1| |/1.1.1| |/1.1| |/1|"
    
    print("\n--- Example 2: Password Requirements ---")
    nodes, edges = translator.parse_horizontal_layout(example2)
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")
    
    # Example 3: Confirmation email timing (Sequencing)
    example3 = "|1|{confirmation_email_received} |1.1|<= @after |1.1.1|<- {1}<$({action})%_> |1.1.2|<- {2}<$({state})%_> |/1.1.2| |/1.1.1| |/1.1| |/1|"
    
    print("\n--- Example 3: Confirmation Email Timing ---")
    nodes, edges = translator.parse_horizontal_layout(example3)
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")
    
    # Example 4: Account verification process (Imperatives and Sequencing)
    example4 = "|1|::({1}<$({action})%_>) |1.1|<= @by |1.1.1|<- ::(Click the link in the email to {1}<$({action})%_>) |/1.1.1| |/1.1| |/1|"
    
    print("\n--- Example 4: Account Verification Process ---")
    nodes, edges = translator.parse_horizontal_layout(example4)
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for node in nodes:
        print(f"Node: {node['id']} - {node['data']['label']} ({node['type']})")
    
    for edge in edges:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['data']['styleType']})")

if __name__ == "__main__":
    test_simple_normcode()
    test_complex_normcode()
    test_real_examples()