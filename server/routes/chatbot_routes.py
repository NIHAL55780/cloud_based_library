"""
Chatbot routes for handling user queries
Interactive rule-based chatbot with context-aware responses
"""

from flask import Blueprint, request, jsonify
import logging
import random
import re

# Initialize Blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
logger = logging.getLogger(__name__)

# Book database (you can expand this with actual books from your library)
BOOKS_DATABASE = {
    'science': [
        {'title': 'The Science of Getting Rich', 'author': 'Wallace D. Wattles'},
        {'title': 'A Brief History of Time', 'author': 'Stephen Hawking'},
        {'title': 'The Selfish Gene', 'author': 'Richard Dawkins'}
    ],
    'mystery': [
        {'title': 'Sherlock Holmes', 'author': 'Arthur Conan Doyle'},
        {'title': 'The Mysterious Affair at Styles', 'author': 'Agatha Christie'},
        {'title': 'The Moonstone', 'author': 'Wilkie Collins'}
    ],
    'fiction': [
        {'title': 'Pride and Prejudice', 'author': 'Jane Austen'},
        {'title': '1984', 'author': 'George Orwell'},
        {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee'}
    ],
    'inspiration': [
        {'title': 'Think and Grow Rich', 'author': 'Napoleon Hill'},
        {'title': 'The Power of Now', 'author': 'Eckhart Tolle'},
        {'title': 'Atomic Habits', 'author': 'James Clear'}
    ]
}

def extract_keywords(query):
    """Extract important keywords from query"""
    # Remove common words
    stop_words = ['what', 'is', 'are', 'the', 'a', 'an', 'do', 'you', 'have', 'can', 'i', 'me', 'my']
    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def find_books_by_query(query):
    """Find books based on user query"""
    query_lower = query.lower()
    found_books = []
    
    # Search by genre
    for genre, books in BOOKS_DATABASE.items():
        if genre in query_lower:
            found_books.extend(books)
    
    # Search by author
    for genre, books in BOOKS_DATABASE.items():
        for book in books:
            if book['author'].lower() in query_lower or book['title'].lower() in query_lower:
                found_books.append(book)
    
    return found_books

def get_intelligent_response(query):
    """Generate intelligent context-aware response"""
    query_lower = query.lower()
    
    # Greeting patterns
    if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'greetings']):
        return "Hello! 👋 I'm your library assistant. I can help you find books, get recommendations, or answer questions about your collection. What would you like to know?"
    
    # Farewell patterns
    if any(word in query_lower for word in ['bye', 'goodbye', 'see you', 'thanks', 'thank you']):
        return "You're welcome! Happy reading! 📚 Feel free to ask me anything anytime."
    
    # Search for specific books
    if any(word in query_lower for word in ['find', 'search', 'looking for', 'show me']):
        books = find_books_by_query(query)
        if books:
            response = "I found these books for you:\n\n"
            for book in books[:5]:  # Limit to 5 results
                response += f"📖 **{book['title']}** by {book['author']}\n"
            return response
        return "I couldn't find specific books matching your query. Try asking about genres like science, mystery, fiction, or inspiration!"
    
    # Genre-specific queries
    if 'science' in query_lower:
        books = BOOKS_DATABASE.get('science', [])
        response = "📚 Science books in your library:\n\n"
        for book in books:
            response += f"• {book['title']} by {book['author']}\n"
        return response + "\nWould you like to know more about any of these?"
    
    if any(word in query_lower for word in ['mystery', 'detective', 'crime', 'thriller']):
        books = BOOKS_DATABASE.get('mystery', [])
        response = "🔍 Mystery & Detective books:\n\n"
        for book in books:
            response += f"• {book['title']} by {book['author']}\n"
        return response + "\nThese are great page-turners!"
    
    if 'fiction' in query_lower:
        books = BOOKS_DATABASE.get('fiction', [])
        response = "📖 Fiction books in your collection:\n\n"
        for book in books:
            response += f"• {book['title']} by {book['author']}\n"
        return response + "\nClassic literature at its finest!"
    
    if any(word in query_lower for word in ['inspiration', 'motivational', 'self-help', 'personal growth']):
        books = BOOKS_DATABASE.get('inspiration', [])
        response = "✨ Inspirational books:\n\n"
        for book in books:
            response += f"• {book['title']} by {book['author']}\n"
        return response + "\nGreat for personal development!"
    
    # Author queries
    if any(word in query_lower for word in ['author', 'written by', 'who wrote', 'writer']):
        # Extract potential author name
        found_books = find_books_by_query(query)
        if found_books:
            authors = list(set([book['author'] for book in found_books]))
            return f"I found books by: {', '.join(authors)}. Would you like to see their books?"
        return "We have books by Agatha Christie, Arthur Conan Doyle, Wilkie Collins, Wallace D. Wattles, and many more! Which author interests you?"
    
    # Recommendation queries
    if any(word in query_lower for word in ['recommend', 'suggestion', 'suggest', 'what should i read']):
        all_books = []
        for books in BOOKS_DATABASE.values():
            all_books.extend(books)
        recommended = random.sample(all_books, min(3, len(all_books)))
        response = "🌟 Here are my top recommendations for you:\n\n"
        for book in recommended:
            response += f"📖 {book['title']} by {book['author']}\n"
        return response + "\nWant recommendations in a specific genre? Just ask!"
    
    # How many books
    if 'how many' in query_lower and 'book' in query_lower:
        total = sum(len(books) for books in BOOKS_DATABASE.values())
        return f"You currently have {total} books in your library across {len(BOOKS_DATABASE)} genres. Would you like to explore any particular genre?"
    
    # Genre list
    if any(word in query_lower for word in ['genre', 'category', 'categories', 'types']):
        genres = ', '.join(BOOKS_DATABASE.keys())
        return f"Your library has books in these genres: {genres}. Which one would you like to explore?"
    
    # Help queries
    if any(word in query_lower for word in ['help', 'what can you do', 'how do you work', 'capabilities']):
        return """I can help you with:
        
📚 **Find books** - Search by title, author, or genre
🎯 **Recommendations** - Get personalized book suggestions  
📖 **Browse genres** - Science, Mystery, Fiction, Inspiration
✍️ **Author info** - Learn about authors in your collection
📊 **Library stats** - See how many books you have

Just ask me anything like:
• "What science books do you have?"
• "Recommend me a mystery book"
• "Books by Agatha Christie"
• "How many books do I have?"

What would you like to know?"""
    
    # Question words - try to be helpful
    if query_lower.startswith(('what', 'which', 'where', 'when', 'who', 'how')):
        keywords = extract_keywords(query)
        if keywords:
            return f"I understand you're asking about {', '.join(keywords)}. Try asking about specific book genres (science, mystery, fiction, inspiration) or authors!"
    
    # Default intelligent response
    keywords = extract_keywords(query)
    if keywords:
        return f"Interesting question about {', '.join(keywords[:3])}! I can help you find books by genre, author, or give recommendations. What specific genre or author are you interested in?"
    
    return "I'm here to help you explore your book collection! You can ask me about:\n• Specific genres (science, mystery, fiction)\n• Book recommendations\n• Authors in your library\n• Searching for specific books\n\nWhat would you like to know?"

@chatbot_bp.route('/query', methods=['POST'])
def query():
    """Handle chatbot queries with intelligent responses"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        user_query = data['query'].strip()
        
        if not user_query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        logger.info(f"Received query: {user_query}")
        
        # Get intelligent response
        response = get_intelligent_response(user_query)
        
        logger.info(f"Generated response: {response[:100]}...")
        
        return jsonify({
            'success': True,
            'response': response,
            'query': user_query
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process query',
            'details': str(e)
        }), 500

@chatbot_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'chatbot',
        'message': 'Interactive chatbot service is running'
    }), 200