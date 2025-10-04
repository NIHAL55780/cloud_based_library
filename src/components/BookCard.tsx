import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Eye, Bookmark } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLibrary } from '@/context/LibraryContext';

interface BookCardProps {
  id: string;
  title: string;
  author: string;
  genre: string;
  cover: string;
}

export const BookCard = ({ id, title, author, genre, cover }: BookCardProps) => {
  const navigate = useNavigate();
  const { isBookmarked, addBookmark, removeBookmark } = useLibrary();
  const bookmarked = isBookmarked(id);

  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ duration: 0.3 }}
      className="glass-effect rounded-xl overflow-hidden group cursor-pointer"
    >
      <div className="relative aspect-[2/3] overflow-hidden">
        <img 
          src={cover} 
          alt={title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-center p-4">
          <Button 
            onClick={() => navigate(`/book/${id}`)}
            className="w-full bg-primary hover:bg-primary/90"
          >
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </Button>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-lg mb-1 line-clamp-1">{title}</h3>
        <p className="text-sm text-muted-foreground mb-2">{author}</p>
        <div className="flex items-center justify-between">
          <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary">
            {genre}
          </span>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => bookmarked ? removeBookmark(id) : addBookmark(id)}
            className="h-8 w-8"
          >
            <Bookmark className={`w-4 h-4 ${bookmarked ? 'fill-primary text-primary' : ''}`} />
          </Button>
        </div>
      </div>
    </motion.div>
  );
};
