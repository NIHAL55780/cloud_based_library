import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { BookOpen, Volume2, Bookmark, ArrowLeft, Star } from 'lucide-react';
import booksData from '@/data/books.json';
import { useLibrary } from '@/context/LibraryContext';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';

export default function BookDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isBookmarked, addBookmark, removeBookmark } = useLibrary();
  const { toast } = useToast();
  const [review, setReview] = useState('');
  const [rating, setRating] = useState(5);

  const book = booksData.find(b => b.id === id);

  if (!book) {
    return (
      <div className="flex min-h-screen">
        <DashboardSidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <p className="text-xl text-muted-foreground">Book not found</p>
        </main>
      </div>
    );
  }

  const bookmarked = isBookmarked(book.id);

  const handleAddReview = () => {
    toast({ title: 'Review Added!', description: 'Your review has been submitted.' });
    setReview('');
  };

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <div className="glass-effect rounded-2xl p-8">
            <div className="grid md:grid-cols-3 gap-8 mb-8">
              <div className="md:col-span-1">
                <img 
                  src={book.cover} 
                  alt={book.title}
                  className="w-full rounded-xl shadow-2xl"
                />
              </div>

              <div className="md:col-span-2">
                <h1 className="text-4xl font-bold mb-2">{book.title}</h1>
                <p className="text-xl text-muted-foreground mb-4">by {book.author}</p>
                
                <div className="flex gap-2 mb-6">
                  <span className="px-3 py-1 rounded-full bg-primary/20 text-primary text-sm">
                    {book.genre}
                  </span>
                  <span className="px-3 py-1 rounded-full bg-secondary/20 text-secondary text-sm">
                    {book.year}
                  </span>
                </div>

                <p className="text-lg mb-8 leading-relaxed">{book.description}</p>

                <div className="flex gap-3">
                  <Button className="bg-primary hover:bg-primary/90">
                    <BookOpen className="w-4 h-4 mr-2" />
                    Read Sample
                  </Button>
                  <Button variant="outline">
                    <Volume2 className="w-4 h-4 mr-2" />
                    Listen
                  </Button>
                  <Button
                    variant={bookmarked ? 'default' : 'outline'}
                    onClick={() => bookmarked ? removeBookmark(book.id) : addBookmark(book.id)}
                  >
                    <Bookmark className={`w-4 h-4 mr-2 ${bookmarked ? 'fill-current' : ''}`} />
                    {bookmarked ? 'Bookmarked' : 'Bookmark'}
                  </Button>
                </div>
              </div>
            </div>

            {/* Reviews Section */}
            <div className="border-t border-border/50 pt-8">
              <h2 className="text-2xl font-bold mb-6">Reviews & Ratings</h2>
              
              <div className="space-y-4 mb-8">
                {book.reviews.map((review, i) => (
                  <div key={i} className="glass-effect p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">{review.user}</span>
                      <div className="flex">
                        {[...Array(review.rating)].map((_, i) => (
                          <Star key={i} className="w-4 h-4 fill-primary text-primary" />
                        ))}
                      </div>
                    </div>
                    <p className="text-muted-foreground">{review.comment}</p>
                  </div>
                ))}
              </div>

              {/* Add Review Form */}
              <div className="glass-effect p-6 rounded-lg">
                <h3 className="text-xl font-semibold mb-4">Add Your Review</h3>
                <div className="mb-4">
                  <label className="block text-sm mb-2">Rating</label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setRating(star)}
                        className="transition-transform hover:scale-110"
                      >
                        <Star 
                          className={`w-6 h-6 ${star <= rating ? 'fill-primary text-primary' : 'text-muted-foreground'}`}
                        />
                      </button>
                    ))}
                  </div>
                </div>
                <Textarea
                  placeholder="Share your thoughts about this book..."
                  value={review}
                  onChange={(e) => setReview(e.target.value)}
                  className="mb-4 glass-effect"
                  rows={4}
                />
                <Button onClick={handleAddReview} className="bg-primary hover:bg-primary/90">
                  Submit Review
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
