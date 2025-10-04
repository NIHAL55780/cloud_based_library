import { useState } from 'react';
import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Play, Pause, SkipBack, SkipForward, Volume2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AudioPlayer() {
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState([30]);
  const [volume, setVolume] = useState([70]);

  // Mock book data
  const book = {
    title: 'The Midnight Library',
    author: 'Matt Haig',
    cover: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=600&fit=crop',
    duration: '8:24:15',
    currentTime: '2:45:30'
  };

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-2xl"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <div className="glass-effect rounded-3xl p-12">
            {/* Album Art */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="aspect-square max-w-md mx-auto mb-8 rounded-2xl overflow-hidden shadow-2xl"
            >
              <img 
                src={book.cover} 
                alt={book.title}
                className="w-full h-full object-cover"
              />
            </motion.div>

            {/* Book Info */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold mb-2">{book.title}</h1>
              <p className="text-lg text-muted-foreground">{book.author}</p>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
              <Slider
                value={progress}
                onValueChange={setProgress}
                max={100}
                step={1}
                className="mb-2"
              />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{book.currentTime}</span>
                <span>{book.duration}</span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-6 mb-8">
              <Button size="icon" variant="ghost" className="h-12 w-12">
                <SkipBack className="w-6 h-6" />
              </Button>
              
              <Button
                size="icon"
                onClick={() => setIsPlaying(!isPlaying)}
                className="h-16 w-16 rounded-full bg-primary hover:bg-primary/90"
              >
                {isPlaying ? (
                  <Pause className="w-8 h-8" />
                ) : (
                  <Play className="w-8 h-8 ml-1" />
                )}
              </Button>
              
              <Button size="icon" variant="ghost" className="h-12 w-12">
                <SkipForward className="w-6 h-6" />
              </Button>
            </div>

            {/* Volume Control */}
            <div className="flex items-center gap-3 max-w-xs mx-auto">
              <Volume2 className="w-5 h-5 text-muted-foreground" />
              <Slider
                value={volume}
                onValueChange={setVolume}
                max={100}
                step={1}
              />
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
