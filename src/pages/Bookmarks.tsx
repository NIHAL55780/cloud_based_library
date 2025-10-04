import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { BookCard } from '@/components/BookCard';
import { useLibrary } from '@/context/LibraryContext';
import booksData from '@/data/books.json';
import { Bookmark } from 'lucide-react';

export default function Bookmarks() {
  const { bookmarks } = useLibrary();
  const bookmarkedBooks = booksData.filter(book => bookmarks.includes(book.id));

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-8 gradient-text flex items-center gap-3">
            <Bookmark className="w-8 h-8" />
            Your Bookmarks
          </h1>

          {bookmarkedBooks.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {bookmarkedBooks.map((book, i) => (
                <motion.div
                  key={book.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <BookCard {...book} />
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="glass-effect rounded-2xl p-12 text-center">
              <Bookmark className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-2">No bookmarks yet</h2>
              <p className="text-muted-foreground">
                Start exploring and bookmark your favorite books!
              </p>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
