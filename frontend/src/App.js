import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Sphere, Box } from '@react-three/drei';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Textarea } from './components/ui/textarea';
import { CheckCircle, Plus, Trash2, User, Zap, Trophy, Star } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// 3D Avatar Component
function Avatar3D({ mood, animation, level }) {
  const [hovered, setHovered] = useState(false);
  
  // Colors based on mood
  const moodColors = {
    happy: '#4ade80',      // green
    excited: '#fbbf24',    // yellow
    neutral: '#6b7280',    // gray
    sad: '#ef4444',        // red
    tired: '#8b5cf6'       // purple
  };
  
  const avatarColor = moodColors[mood] || moodColors.neutral;
  
  // Animation effects
  const getAnimation = () => {
    switch (animation) {
      case 'celebrate':
        return { scale: hovered ? 1.3 : 1.2, position: [0, Math.sin(Date.now() * 0.01) * 0.3, 0] };
      case 'happy_bounce':
        return { scale: hovered ? 1.2 : 1.1, position: [0, Math.sin(Date.now() * 0.008) * 0.2, 0] };
      case 'idle':
      default:
        return { scale: hovered ? 1.1 : 1.0, position: [0, Math.sin(Date.now() * 0.005) * 0.1, 0] };
    }
  };
  
  const animProps = getAnimation();
  
  return (
    <group
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      {/* Avatar Body */}
      <Sphere
        args={[1, 32, 32]}
        position={animProps.position}
        scale={animProps.scale}
      >
        <meshStandardMaterial color={avatarColor} />
      </Sphere>
      
      {/* Eyes */}
      <Sphere args={[0.15, 16, 16]} position={[-0.3, 0.3, 0.8]}>
        <meshStandardMaterial color="#ffffff" />
      </Sphere>
      <Sphere args={[0.15, 16, 16]} position={[0.3, 0.3, 0.8]}>
        <meshStandardMaterial color="#ffffff" />
      </Sphere>
      <Sphere args={[0.08, 16, 16]} position={[-0.3, 0.3, 0.9]}>
        <meshStandardMaterial color="#000000" />
      </Sphere>
      <Sphere args={[0.08, 16, 16]} position={[0.3, 0.3, 0.9]}>
        <meshStandardMaterial color="#000000" />
      </Sphere>
      
      {/* Level indicator above avatar */}
      <Text
        position={[0, 2.5, 0]}
        fontSize={0.5}
        color="#fbbf24"
        anchorX="center"
        anchorY="middle"
      >
        Level {level}
      </Text>
      
      {/* Mood indicator */}
      <Text
        position={[0, -2, 0]}
        fontSize={0.3}
        color={avatarColor}
        anchorX="center"
        anchorY="middle"
      >
        {mood.toUpperCase()}
      </Text>
    </group>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [avatarState, setAvatarState] = useState(null);
  const [newTask, setNewTask] = useState({ title: '', description: '', xp_reward: 10 });
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Initialize or get user
  useEffect(() => {
    initializeUser();
  }, []);

  const initializeUser = async () => {
    try {
      let userId = localStorage.getItem('avatar_user_id');
      
      if (!userId) {
        // Create new user
        const newUser = {
          name: 'Productivity Hero',
          email: 'hero@productivity.com'
        };
        
        const response = await axios.post(`${BACKEND_URL}/api/users`, newUser);
        userId = response.data.id;
        localStorage.setItem('avatar_user_id', userId);
        setUser(response.data);
      } else {
        // Get existing user
        const response = await axios.get(`${BACKEND_URL}/api/users/${userId}`);
        setUser(response.data);
      }
      
      // Load tasks and avatar state
      loadTasks(userId);
      loadAvatarState(userId);
    } catch (error) {
      console.error('Error initializing user:', error);
      setMessage('Error connecting to server. Please refresh the page.');
    }
  };

  const loadTasks = async (userId) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/tasks/${userId}`);
      setTasks(response.data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const loadAvatarState = async (userId) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/avatar-state/${userId}`);
      setAvatarState(response.data);
    } catch (error) {
      console.error('Error loading avatar state:', error);
    }
  };

  const createTask = async () => {
    if (!newTask.title.trim() || !user) return;
    
    setLoading(true);
    try {
      await axios.post(`${BACKEND_URL}/api/tasks?user_id=${user.id}`, newTask);
      setNewTask({ title: '', description: '', xp_reward: 10 });
      setShowTaskForm(false);
      loadTasks(user.id);
      setMessage('Task created successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error creating task:', error);
      setMessage('Error creating task. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId) => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/tasks/complete`, {
        task_id: taskId
      });
      
      // Update user data
      setUser(prev => ({
        ...prev,
        xp: response.data.new_xp,
        level: response.data.new_level,
        avatar_mood: response.data.avatar_mood
      }));
      
      // Reload tasks and avatar state
      loadTasks(user.id);
      loadAvatarState(user.id);
      
      // Show success message
      const levelUpText = response.data.level_up ? ' 🎉 LEVEL UP!' : '';
      setMessage(`+${response.data.xp_gained} XP earned!${levelUpText}`);
      setTimeout(() => setMessage(''), 5000);
    } catch (error) {
      console.error('Error completing task:', error);
      setMessage('Error completing task. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/tasks/${taskId}`);
      loadTasks(user.id);
      setMessage('Task deleted.');
      setTimeout(() => setMessage(''), 2000);
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Awakening your avatar...</p>
        </div>
      </div>
    );
  }

  const xpProgress = (user.xp % 100);
  const xpToNext = 100 - xpProgress;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-white/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Star className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Avatar Productivity
                </h1>
                <p className="text-sm text-gray-600">Your AI companion awaits!</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="px-3 py-1">
                <User className="w-4 h-4 mr-1" />
                {user.name}
              </Badge>
              <Badge variant="outline" className="px-3 py-1 text-indigo-600 border-indigo-200">
                <Trophy className="w-4 h-4 mr-1" />
                Level {user.level}
              </Badge>
              <Badge variant="outline" className="px-3 py-1 text-purple-600 border-purple-200">
                <Zap className="w-4 h-4 mr-1" />
                {user.xp} XP
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Message Banner */}
        {message && (
          <div className="mb-6 p-4 bg-green-100 border border-green-300 rounded-lg text-green-800">
            {message}
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Avatar Section */}
          <Card className="bg-white/60 backdrop-blur-sm border-white/20">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-gray-800">Your Avatar</CardTitle>
              <CardDescription>
                {avatarState?.message || "Your productivity companion is waiting for tasks!"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-96 rounded-lg overflow-hidden bg-gradient-to-b from-sky-100 to-indigo-100">
                <Canvas camera={{ position: [0, 0, 5] }}>
                  <ambientLight intensity={0.6} />
                  <pointLight position={[10, 10, 10]} />
                  <Avatar3D 
                    mood={user.avatar_mood} 
                    animation={avatarState?.animation || 'idle'} 
                    level={user.level}
                  />
                  <OrbitControls enableZoom={false} enablePan={false} />
                </Canvas>
              </div>
              
              {/* XP Progress Bar */}
              <div className="mt-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Progress to Level {user.level + 1}</span>
                  <span className="text-sm text-gray-600">{xpProgress}/100 XP</span>
                </div>
                <Progress value={xpProgress} className="h-3" />
                <p className="text-xs text-gray-500 mt-1">{xpToNext} XP needed for next level</p>
              </div>
            </CardContent>
          </Card>

          {/* Tasks Section */}
          <div className="space-y-6">
            {/* Add Task */}
            <Card className="bg-white/60 backdrop-blur-sm border-white/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xl text-gray-800">Tasks</CardTitle>
                <Button 
                  onClick={() => setShowTaskForm(!showTaskForm)}
                  size="sm"
                  className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Task
                </Button>
              </CardHeader>
              <CardContent>
                {showTaskForm && (
                  <div className="space-y-4 mb-6 p-4 bg-gray-50 rounded-lg">
                    <Input
                      placeholder="Task title..."
                      value={newTask.title}
                      onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                    />
                    <Textarea
                      placeholder="Task description (optional)..."
                      value={newTask.description}
                      onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                    />
                    <Input
                      type="number"
                      placeholder="XP Reward"
                      value={newTask.xp_reward}
                      onChange={(e) => setNewTask(prev => ({ ...prev, xp_reward: parseInt(e.target.value) || 10 }))}
                      min="5"
                      max="100"
                    />
                    <div className="flex gap-2">
                      <Button 
                        onClick={createTask} 
                        disabled={loading || !newTask.title.trim()}
                        className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
                      >
                        Create Task
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => setShowTaskForm(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {/* Task List */}
                <div className="space-y-3">
                  {tasks.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Plus className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No tasks yet. Create your first task to get started!</p>
                    </div>
                  ) : (
                    tasks.map((task) => (
                      <div
                        key={task.id}
                        className={`p-4 rounded-lg border transition-all ${
                          task.completed 
                            ? 'bg-green-50 border-green-200' 
                            : 'bg-white border-gray-200 hover:shadow-sm'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h3 className={`font-medium ${task.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                              {task.title}
                            </h3>
                            {task.description && (
                              <p className={`text-sm mt-1 ${task.completed ? 'text-gray-400' : 'text-gray-600'}`}>
                                {task.description}
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                              <Badge variant="outline" className="text-xs">
                                <Zap className="w-3 h-3 mr-1" />
                                {task.xp_reward} XP
                              </Badge>
                              {task.completed && (
                                <Badge variant="default" className="text-xs bg-green-100 text-green-800">
                                  ✓ Completed
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 ml-4">
                            {!task.completed && (
                              <Button
                                onClick={() => completeTask(task.id)}
                                disabled={loading}
                                size="sm"
                                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </Button>
                            )}
                            <Button
                              onClick={() => deleteTask(task.id)}
                              variant="outline"
                              size="sm"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;