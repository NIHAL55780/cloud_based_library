import { createContext, useContext, useState, ReactNode } from 'react';

interface Book {
  id: string;
  title: string;
  author: string;
  genre: string;
  cover: string;
}

interface LibraryContextType {
  bookmarks: string[];
  addBookmark: (bookId: string) => void;
  removeBookmark: (bookId: string) => void;
  isBookmarked: (bookId: string) => boolean;
}

const LibraryContext = createContext<LibraryContextType | undefined>(undefined);

export const LibraryProvider = ({ children }: { children: ReactNode }) => {
  const [bookmarks, setBookmarks] = useState<string[]>([]);

  const addBookmark = (bookId: string) => {
    setBookmarks(prev => [...prev, bookId]);
  };

  const removeBookmark = (bookId: string) => {
    setBookmarks(prev => prev.filter(id => id !== bookId));
  };

  const isBookmarked = (bookId: string) => {
    return bookmarks.includes(bookId);
  };

  return (
    <LibraryContext.Provider value={{ bookmarks, addBookmark, removeBookmark, isBookmarked }}>
      {children}
    </LibraryContext.Provider>
  );
};

export const useLibrary = () => {
  const context = useContext(LibraryContext);
  if (!context) {
    throw new Error('useLibrary must be used within LibraryProvider');
  }
  return context;
};
