# Book Naming Guide for Optimal Author Detection

This guide shows you the best ways to name your book files when uploading to S3 for automatic author detection.

## ✅ **Recommended Naming Patterns**

### 1. **"Author - Title" Format** (BEST)
```
Arundhati Roy - The God of Small Things.pdf
George Orwell - 1984.pdf
Harper Lee - To Kill a Mockingbird.pdf
```

### 2. **"Title by Author" Format** (EXCELLENT)
```
The Great Gatsby by F. Scott Fitzgerald.pdf
1984 by George Orwell.pdf
To Kill a Mockingbird by Harper Lee.pdf
```

### 3. **"Title, Author" Format** (GOOD)
```
The Great Gatsby, F. Scott Fitzgerald.pdf
1984, George Orwell.pdf
```

### 4. **"Title_Author_Genre" Format** (GOOD)
```
Animal Farm_George Orwell_Fiction.pdf
Pride and Prejudice_Jane Austen_Romance.pdf
```

## ⚠️ **Patterns That May Not Work Well**

### Avoid These Patterns:
```
Title_Author.pdf          # May not detect author correctly
Author_Title.pdf          # May not detect author correctly
SingleWordTitle.pdf       # No author information
```

## 🎯 **Current System Capabilities**

The system can automatically detect these authors:
- Arundhati Roy
- A.P.J. Abdul Kalam / Abdul Kalam / Kalam
- Norman Vincent Peale / Vincent Peale / Peale
- J.K. Rowling / Rowling
- George Orwell / Orwell
- Harper Lee / Lee
- F. Scott Fitzgerald / Fitzgerald
- Ernest Hemingway / Hemingway
- Mark Twain / Twain
- Charles Dickens / Dickens
- Jane Austen / Austen
- Leo Tolstoy / Tolstoy
- Fyodor Dostoevsky / Dostoevsky
- Gabriel Garcia Marquez / Marquez
- Maya Angelou / Angelou
- Toni Morrison / Morrison
- Chimamanda Ngozi Adichie / Adichie

## 📝 **Examples of Good vs Bad Naming**

### ✅ **GOOD Examples:**
```
Arundhati Roy - The God of Small Things.pdf
The Power of Positive Thinking by Norman Vincent Peale.pdf
1984 by George Orwell.pdf
Animal Farm_George Orwell_Fiction.pdf
```

### ❌ **BAD Examples:**
```
The God of Small Things - Arundhati Roy.pdf  # May work but not optimal
Ignited_Minds.pdf                            # Author not detected
wings_of_fire.pdf                           # Author not detected
Simple Title.pdf                            # No author info
```

## 🔧 **Adding New Authors**

To add support for new authors, update the `common_authors` list in `server/routes/library_routes.py`:

```python
common_authors = [
    # Existing authors...
    'Your New Author', 'New Author', 'Author'
]
```

## 📚 **Current Books Status**

Based on your current S3 bucket:
- ✅ "Arundhati Roy - The God of Small Things.pdf" → **Author: Arundhati Roy**
- ✅ "The Power of Positive Thinking - Norman Vincent Peale.pdf" → **Author: Norman Vincent Peale**
- ❌ "Ignited_Minds.pdf" → **Author: Minds** (needs renaming)
- ❌ "wings_of_fire.pdf" → **Author: of** (needs renaming)

## 🚀 **Quick Fix for Existing Books**

To fix the current books, rename them in S3:
1. "Ignited_Minds.pdf" → "Ignited Minds by A.P.J. Abdul Kalam.pdf"
2. "wings_of_fire.pdf" → "Wings of Fire by A.P.J. Abdul Kalam.pdf"

This will automatically update the author information in your frontend!
