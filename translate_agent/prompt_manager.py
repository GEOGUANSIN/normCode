"""
NormCode Prompt Database - Ultra Simple Version
"""

import sqlite3
import os
from typing import Optional
from datetime import datetime


class PromptDatabase:
    """Simple SQLite database for prompts"""
    
    def __init__(self, db_path: str = "sequence/normcode_prompts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create prompts table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    agent_type TEXT NOT NULL,
                    prompt_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    PRIMARY KEY (agent_type, prompt_type)
                )
            """)
            conn.commit()
    
    def get_prompt(self, agent_type: str, prompt_type: str) -> Optional[str]:
        """Get prompt content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content FROM prompts 
                WHERE agent_type = ? AND prompt_type = ?
            """, (agent_type, prompt_type))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def save_prompt(self, agent_type: str, prompt_type: str, content: str):
        """Save prompt content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO prompts (agent_type, prompt_type, content)
                VALUES (?, ?, ?)
            """, (agent_type, prompt_type, content))
            conn.commit()


class PromptManager:
    """Simple prompt manager with two modes"""
    
    def __init__(self, mode: str = "database", db_path: str = "sequence/normcode_prompts.db", prompts_dir: str = "translate_agent/phase_agent/prompts"):
        self.mode = mode
        self.db = PromptDatabase(db_path) if mode == "database" else None
        self.prompts_dir = prompts_dir
        
        # File mappings
        self.files = {
            "ntd_1_establishing_main_question.txt": ("question_sequencing", "question_type_analysis"),
            "ntd_2_sentence_chunking.txt": ("question_sequencing", "sentence_chunking"),
            "ntd_3_chunk_question_generation.txt": ("question_sequencing", "chunk_question_generation"),
            "iqa_1_question_structure_analysis.txt": ("in_question_analysis", "question_structure_analysis"),
            "iqa_2_clause_analysis.txt": ("in_question_analysis", "clause_analysis"),
            "iqa_2b_phase2_draft_creation.txt": ("in_question_analysis", "phase2_draft_creation"),
            "iqa_3_template_creation.txt": ("in_question_analysis", "template_creation"),
            "normcode_context.txt": ("general", "context"),
            "direct_prompt.txt": ("general", "direct")
        }
        
        if mode == "database":
            self._load_files_to_db()
    
    def get_prompt(self, agent_type: str, prompt_type: str) -> Optional[str]:
        """Get prompt content"""
        if self.mode == "database":
            return self.db.get_prompt(agent_type, prompt_type)
        else:
            return self._get_from_file(agent_type, prompt_type)
    
    def _get_from_file(self, agent_type: str, prompt_type: str) -> Optional[str]:
        """Get prompt from file"""
        for filename, (file_agent, file_type) in self.files.items():
            if file_agent == agent_type and file_type == prompt_type:
                file_path = os.path.join(self.prompts_dir, filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return f.read().strip()
                    except:
                        pass
        return None
    
    def _load_files_to_db(self):
        """Load files into database"""
        if not os.path.exists(self.prompts_dir):
            return
        
        for filename, (agent_type, prompt_type) in self.files.items():
            file_path = os.path.join(self.prompts_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    self.db.save_prompt(agent_type, prompt_type, content)
                except:
                    pass


class PromptSyncer:
    """Simple sync between files and database"""
    
    def __init__(self, db_path: str = "sequence/normcode_prompts.db", prompts_dir: str = "translate_agent/phase_agent/prompts"):
        self.db = PromptDatabase(db_path)
        self.prompts_dir = prompts_dir
        
        self.files = {
            "ntd_1_establishing_main_question.txt": ("question_sequencing", "question_type_analysis"),
            "ntd_2_sentence_chunking.txt": ("question_sequencing", "sentence_chunking"),
            "ntd_3_chunk_question_generation.txt": ("question_sequencing", "chunk_question_generation"),
            "iqa_1_question_structure_analysis.txt": ("in_question_analysis", "question_structure_analysis"),
            "iqa_2_clause_analysis.txt": ("in_question_analysis", "clause_analysis"),
            "iqa_2b_phase2_draft_creation.txt": ("in_question_analysis", "phase2_draft_creation"),
            "iqa_3_template_creation.txt": ("in_question_analysis", "template_creation"),
            "normcode_context.txt": ("general", "context"),
            "direct_prompt.txt": ("general", "direct")
        }
    
    def files_to_db(self) -> int:
        """Sync files to database"""
        if not os.path.exists(self.prompts_dir):
            return 0
        
        count = 0
        for filename, (agent_type, prompt_type) in self.files.items():
            file_path = os.path.join(self.prompts_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    self.db.save_prompt(agent_type, prompt_type, content)
                    count += 1
                except:
                    pass
        return count
    
    def db_to_files(self) -> int:
        """Sync database to files"""
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir, exist_ok=True)
        
        count = 0
        for filename, (agent_type, prompt_type) in self.files.items():
            content = self.db.get_prompt(agent_type, prompt_type)
            if content:
                try:
                    file_path = os.path.join(self.prompts_dir, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    count += 1
                except:
                    pass
        return count


if __name__ == "__main__":
    print("=== NormCode Prompt Database Demo ===\n")
    
    # Use existing prompts directory
    prompts_dir = "translate_agent/phase_agent/prompts"
    
    if not os.path.exists(prompts_dir):
        print(f"Error: Prompts directory '{prompts_dir}' not found!")
        print("Please run this from the project root directory")
        exit(1)
    
    print(f"Using existing prompts directory: {prompts_dir}")
    
    # List existing prompt files
    print("\nExisting prompt files:")
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.txt'):
            print(f"  - {filename}")
    
    print(f"\n--- PromptManager Demo ---")
    
    # Database mode
    print("\n1. Database Mode:")
    db_manager = PromptManager(mode="database", db_path="sequence/normcode_prompts.db", prompts_dir=prompts_dir)
    prompt = db_manager.get_prompt("question_sequencing", "question_type_analysis")
    if prompt:
        print(f"   Prompt preview: {prompt[:100]}...")
    else:
        print("   No prompt found")
    
    # File mode
    print("\n2. File Mode:")
    file_manager = PromptManager(mode="file", prompts_dir=prompts_dir)
    prompt = file_manager.get_prompt("question_sequencing", "sentence_chunking")
    if prompt:
        print(f"   Prompt preview: {prompt[:100]}...")
    else:
        print("   No prompt found")
    
    print(f"\n--- PromptSyncer Demo ---")
    
    # Sync demo
    syncer = PromptSyncer(prompts_dir=prompts_dir)
    
    print("\n3. Sync Files to Database:")
    count = syncer.files_to_db()
    print(f"   Synced {count} prompts to database")
    
    print("\n4. Test database sync back to files:")
    # Get current content from database
    current_content = syncer.db.get_prompt("question_sequencing", "question_type_analysis")
    if current_content:
        print(f"   Current DB content preview: {current_content[:100]}...")
    
    # Test sync back (this will overwrite files with DB content)
    count = syncer.db_to_files()
    print(f"   Synced {count} prompts to files")
    
    print(f"\n--- Direct Database Demo ---")
    
    # Direct database usage
    db = PromptDatabase("sequence/demo.db")
    db.save_prompt("test", "example", "This is a test prompt")
    content = db.get_prompt("test", "example")
    print(f"\n5. Direct DB: {content}")
    
    print(f"\n=== Demo Complete ===")
    print(f"Database file: sequence/normcode_prompts.db")
    print(f"Demo database: sequence/demo.db")
    print(f"Prompts directory: {prompts_dir}")
    