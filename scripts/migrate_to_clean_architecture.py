#!/usr/bin/env python3
"""
Migration Script: Old Structure → Clean Architecture
Automates the restructuring of the codebase
"""
import os
import shutil
from pathlib import Path


def create_directory_structure():
    """Create the new directory structure"""
    print("📁 Creating new directory structure...")
    
    directories = [
        "app/orchestrators",
        "app/intelligence/prompts",
        "app/intelligence/tools",
        "app/addons/search",
        "app/addons/memory",
        "app/addons/personalization",
        "app/domain/products",
        "app/domain/users",
        "app/domain/pricing",
        "app/domain/recommendations",
        "app/domain/conversations",
        "app/infrastructure/db",
        "app/infrastructure/cache",
        "app/infrastructure/vector",
        "app/infrastructure/storage",
        "app/realtime/events",
        "app/middleware",
        "app/schemas",
        "app/utils",
        "infra/k8s",
        "infra/terraform",
        "infra/docker",
        "scripts",
        "tests/unit/domain",
        "tests/unit/addons",
        "tests/unit/intelligence",
        "tests/integration/orchestrators",
        "tests/integration/api",
        "tests/e2e",
        "docs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if directory.startswith("app/"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Package"""')
    
    print("✅ Directory structure created")


def create_init_files():
    """Create __init__.py files in all directories"""
    print("📝 Creating __init__.py files...")
    
    for root, dirs, files in os.walk("app"):
        for dir_name in dirs:
            if not dir_name.startswith("__"):
                init_file = Path(root) / dir_name / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""Package"""')
    
    print("✅ __init__.py files created")


def backup_old_structure():
    """Backup the old structure before migration"""
    print("💾 Creating backup of old structure...")
    
    backup_dirs = ["app/services", "app/models", "app/core", "app/websocket"]
    backup_root = Path("backup_old_structure")
    backup_root.mkdir(exist_ok=True)
    
    for dir_path in backup_dirs:
        if Path(dir_path).exists():
            dest = backup_root / dir_path
            shutil.copytree(dir_path, dest, dirs_exist_ok=True)
            print(f"  ✅ Backed up {dir_path}")
    
    print("✅ Backup complete")


def generate_migration_report():
    """Generate a report of what needs to be migrated"""
    print("\n📊 Migration Report")
    print("=" * 60)
    
    old_files = {
        "Infrastructure Layer": [
            "app/services/redis_service.py",
            "app/services/firestore_service.py",
        ],
        "Domain Layer": [
            "app/services/product_service.py",
            "app/services/user_service.py",
            "app/services/conversation_service.py",
        ],
        "Intelligence Layer": [
            "app/services/llm_service.py",
        ],
        "Orchestrators": [
            "app/services/chat_service.py",
            "app/services/search_service.py",
            "app/services/image_service.py",
        ],
        "Schemas": [
            "app/models/requests.py",
            "app/models/responses.py",
        ],
        "API Layer": [
            "app/api/v1/endpoints/chat.py",
            "app/api/v1/endpoints/search.py",
            "app/api/v1/endpoints/products.py",
            "app/api/v1/endpoints/users.py",
            "app/api/v1/endpoints/images.py",
        ],
    }
    
    for layer, files in old_files.items():
        print(f"\n{layer}:")
        for file_path in files:
            exists = "✅" if Path(file_path).exists() else "❌"
            print(f"  {exists} {file_path}")
    
    print("\n" + "=" * 60)


def create_readme():
    """Create README for the new structure"""
    readme_content = """# Walmart AI Assistant - Clean Architecture

## 🏗️ Architecture

This project follows a strict layered architecture. See `ARCHITECTURE.md` for details.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run the application
python main.py
```

## 📁 Structure

```
app/
├── api/               # Layer 1: Dumb APIs
├── orchestrators/     # Layer 2: Workflow logic
├── intelligence/      # Layer 3: LLM + function calling
├── addons/            # Layer 4: Search, memory, personalization
├── domain/            # Layer 5: Business logic
├── infrastructure/    # Layer 6: DB, cache, storage
├── realtime/          # WebSocket handlers
├── middleware/        # Auth, rate limit, logging
├── schemas/           # Pydantic models
└── utils/             # Shared helpers
```

## 📚 Documentation

- `ARCHITECTURE.md` - Detailed architecture documentation
- `MIGRATION_GUIDE.md` - Migration guide from old structure
- `docs/` - Additional documentation

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific layer tests
pytest tests/unit/domain/
pytest tests/integration/orchestrators/
```

## 🔒 Architecture Rules

1. APIs never talk to DB
2. LLMs never talk to DB
3. Domain never knows LLM exists
4. Orchestrator is the only "god"
5. If a file imports FastAPI + business logic → you fucked up

## 📊 Monitoring

- Health: `GET /api/v1/health/`
- Metrics: `GET /api/v1/health/stats`
- Docs: `GET /docs` (dev only)

## 🤝 Contributing

1. Read `ARCHITECTURE.md`
2. Follow the layer rules
3. Write tests
4. Update documentation
"""
    
    Path("README_NEW.md").write_text(readme_content)
    print("✅ Created README_NEW.md")


def main():
    """Main migration function"""
    print("🚀 Starting Clean Architecture Migration")
    print("=" * 60)
    
    # Step 1: Backup
    backup_old_structure()
    
    # Step 2: Create structure
    create_directory_structure()
    create_init_files()
    
    # Step 3: Generate report
    generate_migration_report()
    
    # Step 4: Create documentation
    create_readme()
    
    print("\n" + "=" * 60)
    print("✅ Migration preparation complete!")
    print("\n📋 Next Steps:")
    print("1. Review ARCHITECTURE.md")
    print("2. Review MIGRATION_GUIDE.md")
    print("3. Start migrating files layer by layer")
    print("4. Update imports")
    print("5. Run tests")
    print("6. Deploy")
    print("\n💡 Tip: Migrate one layer at a time, starting with Infrastructure")


if __name__ == "__main__":
    main()
