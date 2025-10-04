import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Sparkles, RefreshCw } from 'lucide-react';
import recommendationsData from '@/data/recommendations.json';
import { useToast } from '@/hooks/use-toast';

export default function Recommendations() {
  const { toast } = useToast();

  const handleRegenerate = () => {
    toast({ 
      title: 'Generating Recommendations...', 
      description: 'AI is analyzing your reading patterns.' 
    });
    setTimeout(() => {
      toast({ 
        title: 'Done!', 
        description: 'Your recommendations have been updated.' 
      });
    }, 2000);
  };

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold gradient-text flex items-center gap-3">
                <Sparkles className="w-8 h-8" />
                Your AI Book Recommendations
              </h1>
              <p className="text-muted-foreground mt-2">
                Personalized picks based on your reading history
              </p>
            </div>
            <Button onClick={handleRegenerate} className="bg-secondary hover:bg-secondary/90">
              <RefreshCw className="w-4 h-4 mr-2" />
              Regenerate
            </Button>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendationsData.map((rec, i) => (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -8 }}
                className="glass-effect rounded-xl overflow-hidden group cursor-pointer"
              >
                <div className="relative aspect-[2/3]">
                  <img 
                    src={rec.cover} 
                    alt={rec.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                </div>
                
                <div className="p-6">
                  <h3 className="font-semibold text-xl mb-2">{rec.title}</h3>
                  <p className="text-sm text-muted-foreground mb-3">{rec.author}</p>
                  <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary inline-block mb-3">
                    {rec.genre}
                  </span>
                  <div className="flex items-start gap-2 text-sm">
                    <Sparkles className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                    <p className="text-muted-foreground">{rec.reason}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </main>
    </div>
  );
}
