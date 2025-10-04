import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { BookCard } from '@/components/BookCard';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search } from 'lucide-react';
import booksData from '@/data/books.json';

export default function Dashboard() {
  const [searchQuery, setSearchQuery] = useState('');
  const [genreFilter, setGenreFilter] = useState('all');
  const [languageFilter, setLanguageFilter] = useState('all');

  const genres = useMemo(() => ['all', ...new Set(booksData.map(book => book.genre))], []);
  const languages = useMemo(() => ['all', ...new Set(booksData.map(book => book.language))], []);

  const filteredBooks = useMemo(() => {
    return booksData.filter(book => {
      const matchesSearch = book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          book.author.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesGenre = genreFilter === 'all' || book.genre === genreFilter;
      const matchesLanguage = languageFilter === 'all' || book.language === languageFilter;
      return matchesSearch && matchesGenre && matchesLanguage;
    });
  }, [searchQuery, genreFilter, languageFilter]);

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-8 gradient-text">Your Library</h1>
          
          {/* Search and Filters */}
          <div className="glass-effect p-6 rounded-xl mb-8">
            <div className="grid md:grid-cols-4 gap-4">
              <div className="md:col-span-2 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search books or authors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 glass-effect"
                />
              </div>
              
              <Select value={genreFilter} onValueChange={setGenreFilter}>
                <SelectTrigger className="glass-effect">
                  <SelectValue placeholder="Genre" />
                </SelectTrigger>
                <SelectContent>
                  {genres.map(genre => (
                    <SelectItem key={genre} value={genre}>
                      {genre === 'all' ? 'All Genres' : genre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={languageFilter} onValueChange={setLanguageFilter}>
                <SelectTrigger className="glass-effect">
                  <SelectValue placeholder="Language" />
                </SelectTrigger>
                <SelectContent>
                  {languages.map(lang => (
                    <SelectItem key={lang} value={lang}>
                      {lang === 'all' ? 'All Languages' : lang}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Books Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filteredBooks.map((book, i) => (
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

          {filteredBooks.length === 0 && (
            <div className="text-center py-20">
              <p className="text-xl text-muted-foreground">No books found matching your criteria.</p>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
