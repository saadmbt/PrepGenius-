import React from 'react';
import { Route, Routes } from 'react-router-dom';
import StudentDashboardLayout from '../layouts/StudentDashboardLayout';
import Studentmainpage from '../pages/Dashboard/Studentmainpage';
import QuizDetailspage from '../pages/Dashboard/QuizDetailspage';
import FlashcardsSection from '../components/dashboard/FlashcardDeckSection';
import FlashcardStudy from '../components/dashboard/FlashCardStudy';
import QuizSetup from '../pages/Dashboard/QuizSetup';
import Quiz from '../pages/Dashboard/Quiz';
import Upload from '../pages/Dashboard/uploadpage';
import Quizzespage from '../pages/Dashboard/Quizzespage';
import JoinGroup from '../components/groups/Joingroup';

const StudentRoutes =[
  {
    index: true,
    element: <Studentmainpage />,
  },
  {
    path: 'upload',
    element: <Upload />,
  },
  {
    path: 'quiz',
    element: <Quiz />,
  },
  {
    path: 'upload/quizsetup',
    element: <QuizSetup />,
  },
  {
    path: 'quizzes',
    element: <Quizzespage />,
  },
  {
    path: 'quizzes/:id',
    element: <QuizDetailspage />,
  },
  {
    path: 'flashcards',
    element: <FlashcardsSection/>,
  },
  {
    path: 'flashcards/study/:id',
    element: <FlashcardStudy />,
  },
  { 
    path: "join-group/:token",
    element: <JoinGroup />,
  }

]
  // return (
  //   <Routes>
  //     <Route path="/Dashboard" element={<StudentDashboardLayout />}>
  // );


export default StudentRoutes;
