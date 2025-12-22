# Absolute Database Paths Support

## Quick Answer

✅ **Yes! Absolute database paths are fully supported.**

The database path can be either:
- **Relative**: `orchestration.db` (relative to current working directory)
- **Absolute**: `C:\Users\YourName\databases\my_db.sqlite` (Windows) or `/home/user/databases/my_db.sqlite` (Linux/Mac)

## How It Works

### The System Already Supports It

1. **Database Class**: Uses Python's `Path()` which handles both absolute and relative paths
2. **SQLite3**: Natively supports absolute paths
3. **File Operations**: All file checks use `os.path.exists()` which works with absolute paths

### Example Usage

#### Windows Absolute Path
```
Database Path: C:\Users\ProgU\databases\normcode_orchestration.db
```

#### Linux/Mac Absolute Path
```
Database Path: /home/user/databases/normcode_orchestration.db
```

#### Relative Path (Still Works)
```
Database Path: orchestration.db
```

## Configuration Loading

When you save a configuration with an absolute database path:
- The absolute path is stored in metadata
- It's automatically loaded when you load that configuration
- No path resolution issues

### Example Workflow

```
1. Set Database Path: C:\Users\ProgU\databases\project1.db
2. Execute a run
3. Configuration is saved with absolute path

Later:
1. Load configuration from that run
2. Database Path auto-populates: C:\Users\ProgU\databases\project1.db
3. Ready to use!
```

## Benefits of Absolute Paths

### ✅ Consistent Location
- Database always in the same place
- Not affected by working directory changes
- Easy to find and manage

### ✅ Multiple Projects
```
Project A: C:\Projects\ProjectA\orchestration.db
Project B: C:\Projects\ProjectB\orchestration.db
Project C: C:\Projects\ProjectC\orchestration.db
```

### ✅ Shared Databases
```
Team Database: \\server\shared\normcode\team_db.sqlite
```

### ✅ Portable Configurations
When you load a configuration with an absolute path:
- Works from any working directory
- Same database location
- No path resolution issues

## How to Use

### Setting an Absolute Path

1. Go to sidebar → "💾 Checkpoint Settings"
2. In "Database Path" field, enter absolute path:
   ```
   Windows: C:\Users\YourName\databases\my_db.sqlite
   Linux/Mac: /home/username/databases/my_db.sqlite
   ```
3. Execute a run (path is saved in configuration)

### Loading Configuration with Absolute Path

1. Load configuration from previous run
2. Database Path field auto-populates with absolute path
3. Ready to use immediately

## Technical Details

### Path Handling

```python
# The database class uses Path() which handles both:
from pathlib import Path

db_path = Path("orchestration.db")  # Relative - works
db_path = Path("C:/Users/Name/db.sqlite")  # Absolute - works
db_path = Path("/home/user/db.sqlite")  # Absolute - works

# SQLite3 connection works with Path objects:
conn = sqlite3.connect(db_path)  # Works for both!
```

### Directory Creation

If the directory doesn't exist, it's automatically created:

```python
# Database class automatically creates parent directories
self.db_path.parent.mkdir(parents=True, exist_ok=True)
```

So even if `C:\Users\YourName\databases\` doesn't exist, it will be created!

## Common Use Cases

### Use Case 1: Project-Specific Databases

```
Project Root: C:\Projects\NormCodeProject\
Database: C:\Projects\NormCodeProject\data\orchestration.db
```

### Use Case 2: Centralized Storage

```
All Databases: D:\NormCodeDatabases\
Project A: D:\NormCodeDatabases\project_a.db
Project B: D:\NormCodeDatabases\project_b.db
```

### Use Case 3: Shared Team Database

```
Network Path: \\server\team\normcode\shared_db.sqlite
```

## Notes

### Path Format

- **Windows**: Use backslashes `\` or forward slashes `/` (Python handles both)
  - `C:\Users\Name\db.sqlite` ✅
  - `C:/Users/Name/db.sqlite` ✅

- **Linux/Mac**: Use forward slashes `/`
  - `/home/user/db.sqlite` ✅

### Relative Path Behavior

If you use a relative path like `orchestration.db`:
- It's resolved relative to the **current working directory**
- This can change depending on how you run the app
- Absolute paths avoid this uncertainty

### Configuration Loading

When loading a configuration:
- **Absolute paths**: Load exactly as saved (reliable)
- **Relative paths**: Resolved relative to current working directory (may differ)

## Summary

✅ **Absolute paths are fully supported**  
✅ **No special configuration needed**  
✅ **Just enter the absolute path in the Database Path field**  
✅ **It will be saved and loaded automatically**  

**Recommendation**: Use absolute paths for consistency and reliability, especially when working with multiple projects or sharing configurations!

