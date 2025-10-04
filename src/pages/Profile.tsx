import { motion } from 'framer-motion';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { User, Mail, BookOpen } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useLibrary } from '@/context/LibraryContext';

export default function Profile() {
  const { user } = useAuth();
  const { bookmarks } = useLibrary();

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      
      <main className="flex-1 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-8 gradient-text">Your Profile</h1>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Profile Info */}
            <div className="lg:col-span-2 glass-effect rounded-2xl p-8">
              <h2 className="text-2xl font-semibold mb-6">Account Information</h2>
              
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    type="text"
                    value={user?.name || ''}
                    readOnly
                    className="glass-effect"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={user?.email || ''}
                    readOnly
                    className="glass-effect"
                  />
                </div>

                <Button className="bg-primary hover:bg-primary/90">
                  Update Profile
                </Button>
              </div>
            </div>

            {/* Stats */}
            <div className="space-y-6">
              <div className="glass-effect rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-lg bg-primary/20">
                    <BookOpen className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Bookmarks</p>
                    <p className="text-2xl font-bold">{bookmarks.length}</p>
                  </div>
                </div>
              </div>

              <div className="glass-effect rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-lg bg-secondary/20">
                    <User className="w-6 h-6 text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Member Since</p>
                    <p className="text-lg font-semibold">2024</p>
                  </div>
                </div>
              </div>

              <div className="glass-effect rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-lg bg-accent/20">
                    <Mail className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <p className="text-lg font-semibold text-primary">Active</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
