# Phase 1 Testing Plan: QuestionSequencingAgent

## Overview

This document outlines the comprehensive testing strategy for the QuestionSequencingAgent (Phase 1) using the complete NormCode infrastructure including LLMFactory, prompt database, and NormCode terminology context.

## Testing Objectives

1. **Integration Testing**: Verify seamless integration between LLMFactory, prompt database, and QuestionSequencingAgent
2. **Context-Aware Processing**: Test the agent's ability to use NormCode terminology context for improved question generation
3. **Real-World Examples**: Validate against the account creation example from the documentation

## Test Architecture

### Components Integration
```
LLMFactory (LLM Client)
    ↓
PromptDatabase (Prompt Management)
    ↓
QuestionSequencingAgent (Phase 1 Processing)
    ↓
NormCode Terminology Context (Domain Knowledge)
```

### Test Data Sources
- **LLM Client**: LLMFactory with local or cloud endpoint
- **Prompts**: PromptDatabase with question_sequencing agent prompts
- **Context**: NormCode terminology from NormCode_terms/ directory
- **Test Cases**: Account creation example from complete_examples/account_creation.md

## Test Cases

### Test Case 1: Basic Integration Test
**Objective**: Verify basic functionality without context
**Input**: "Create a user account with email and password"
**Expected**: 
- Main question type: "how"
- Target: "{main_process}"
- Condition: "@by"
- Question: "$how?({main_process}, @by)"

### Test Case 2: Context-Enhanced Processing
**Objective**: Test improved question generation with NormCode terminology
**Input**: "Create a user account with email and password"
**Context**: NormCode syntax reference and terminology
**Expected**: 
- More precise question generation
- Better understanding of NormCode operators
- Enhanced metadata tracking

