import React, { useState } from 'react';
import { Upload as UploadIcon } from 'lucide-react';
import UploadTabs from '../../components/dashboard/UploadTabs';
import FileUpload from '../../components/dashboard/FileUpload';
import TextUpload from '../../components/dashboard/TextUpload';
import { useNavigate } from 'react-router-dom';
import { uploadLesson } from '../../services/StudentService';
import getJWT, { isTokenExpired } from '../../services/authService';
import toast from 'react-hot-toast';

export default function ProfUpload({ onComplete }) {
  const [activeTab, setActiveTab] = useState('file');
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  const refreshTokenIfNeeded = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }
    try {
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      if (isTokenExpired(tokenData)) {
        // Assuming uid is stored in localStorage or elsewhere
        const uid = localStorage.getItem('uid');
        if (!uid) {
          return null;
        }
        const newToken = await getJWT(uid);
        if (newToken) {
          localStorage.setItem('access_token', newToken);
          return newToken;
        }
        return null;
      }
      return token;
    } catch (error) {
      console.error('Error parsing token:', error);
      return null;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (activeTab === 'file' && file && file.size > 10 * 1024 * 1024) {
      toast.error('File must be less than 10MB.');
      return;
    }
    if (activeTab === 'text' && text.length > 10000) {
      toast.error('Text must be less than 10000 characters.');
      return;
    }
    if (!file && activeTab === 'file') {
      toast('Please select a file to upload.', {
        icon: '❗',
        style: {
          size: '1rem',
          fontSize: '1rem',
        },
      });
      return;
    }
    const data = activeTab === 'file' ? (file ? file : null) : (text.trim() ? text : null);

    setIsUploading(true);
    try {
      if ((activeTab === 'file' && !file) || (activeTab === 'text' && !text.trim())) {
        toast('Please select a file or enter valid text to upload.', {
          icon: '❗❗',
          style: {
            size: '1rem',
            fontSize: '1rem',
          },
        });
        setIsUploading(false);
        return;
      }

      const validToken = await refreshTokenIfNeeded();
      if (!validToken) {
        toast.error('Authentication required. Please log in again.');
        setIsUploading(false);
        return;
      }

      // Get username from localStorage or other source
      const username = JSON.parse(localStorage.getItem('_us_unr')).username || 'unknown';

      // uploadLesson reads token from localStorage, so token is updated there
      const response = await uploadLesson(data, title, activeTab, username);

      const LessonID = response && response.lesson_id ? response.lesson_id : null;
      if (!LessonID) {
        toast.error('Failed to retrieve Lesson ID. Please try again.');
        setIsUploading(false);
        return;
      }

      console.log('Lesson uploaded ID:', LessonID);
      setIsUploading(false);
      onComplete(LessonID);
      navigate('/professor/upload/quizsetup');
    } catch (error) {
      console.error('Error uploading lesson:', error);
      toast.error(error.message || 'Failed to upload lesson. Please try again.');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-start justify-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload Learning Material</h1>
        </div>
        <p className="text-gray-600 text-center">Add new content to your learning library</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <UploadTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {activeTab === 'file' ? (
          <FileUpload onFileSelect={setFile} setTitle={setTitle} />
        ) : (
          <TextUpload value={text} onChange={setText} />
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Your Lesson Title"
              className="w-full px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isUploading || (!file && !text) || !title}
          className={
            `w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg
            text-white font-medium transition-colors duration-200
            ${isUploading || (!file && !text) || !title
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
            }`
          }
        >
          {isUploading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
              Uploading...
            </>
          ) : (
            <>
              <UploadIcon className="h-5 w-5" />
              Upload Material
            </>
          )}
        </button>
      </form>
    </div>
  );
}
