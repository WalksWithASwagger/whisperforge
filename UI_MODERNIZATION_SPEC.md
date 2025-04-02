# WhisperForge UI Modernization Specification

This document outlines the technical and design requirements for Phase 2 of the WhisperForge implementation plan, focusing on transitioning from Streamlit to a modern React-based frontend with advanced UI capabilities.

## 1. Design System

### 1.1 Visual Language

The WhisperForge design system will follow these principles:

- **Modern Minimalism**: Clean, focused interface with ample whitespace
- **Content-First**: Prioritize content display and editing workflows
- **Professional Aesthetic**: Dark mode primary theme with accent colors
- **Responsive Design**: Fully responsive from mobile to large desktop displays

### 1.2 Color Palette

```css
:root {
  /* Primary colors */
  --primary-900: #1a1020;
  --primary-800: #2a1a30;
  --primary-700: #3a2040;
  --primary-600: #4a3050;
  --primary-500: #5a4060;
  
  /* Accent colors */
  --accent-500: #7928ca;
  --accent-400: #9750dd;
  --accent-300: #b77dea;
  
  /* UI colors */
  --success: #0cce6b;
  --warning: #ffb224;
  --error: #ff4757;
  --info: #2e86de;
  
  /* Neutral colors */
  --neutral-900: #121212;
  --neutral-800: #1e1e1e;
  --neutral-700: #2d2d2d;
  --neutral-600: #393939;
  --neutral-500: #5c5c5c;
  --neutral-400: #919191;
  --neutral-300: #b3b3b3;
  --neutral-200: #d1d1d1;
  --neutral-100: #f5f5f5;
  
  /* Text colors */
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-tertiary: rgba(255, 255, 255, 0.5);
}
```

### 1.3 Typography

```css
:root {
  /* Font families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', Menlo, Monaco, Consolas, monospace;
  
  /* Font sizes */
  --text-xs: 0.75rem;   /* 12px */
  --text-sm: 0.875rem;  /* 14px */
  --text-base: 1rem;    /* 16px */
  --text-lg: 1.125rem;  /* 18px */
  --text-xl: 1.25rem;   /* 20px */
  --text-2xl: 1.5rem;   /* 24px */
  --text-3xl: 1.875rem; /* 30px */
  --text-4xl: 2.25rem;  /* 36px */
  
  /* Line heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

### 1.4 Components & Animations

Key components will include motion effects for enhanced user experience:

- Microinteractions on hover, click, and focus states
- Transition effects between pipeline steps
- Progress indicators with fluid animations
- Content reveal animations for generated content

## 2. Application Architecture

### 2.1 Frontend Stack

```
Next.js (React framework)
├── Tailwind CSS (styling)
├── Framer Motion (animations)
├── Zustand (state management)
├── React Query (data fetching)
└── Socket.io (real-time updates)
```

### 2.2 State Management

```typescript
// Zustand store example
interface PipelineState {
  steps: PipelineStep[];
  activeStep: string | null;
  results: Record<string, any>;
  status: 'idle' | 'running' | 'completed' | 'failed';
  
  // Actions
  addStep: (step: PipelineStep) => void;
  removeStep: (stepId: string) => void;
  reorderSteps: (fromIndex: number, toIndex: number) => void;
  setActiveStep: (stepId: string | null) => void;
  updateStepConfig: (stepId: string, config: Partial<StepConfig>) => void;
  runPipeline: () => Promise<void>;
  cancelPipeline: () => void;
}

export const usePipelineStore = create<PipelineState>((set, get) => ({
  steps: [],
  activeStep: null,
  results: {},
  status: 'idle',
  
  addStep: (step) => set((state) => ({ 
    steps: [...state.steps, step] 
  })),
  
  removeStep: (stepId) => set((state) => ({ 
    steps: state.steps.filter(step => step.id !== stepId) 
  })),
  
  // Additional actions omitted for brevity
}));
```

### 2.3 API Integration

```typescript
// React Query example for API integration
export const usePipelineRun = (pipelineId: string) => {
  return useQuery(
    ['pipeline', pipelineId],
    () => fetch(`/api/pipelines/${pipelineId}`).then(res => res.json()),
    {
      refetchInterval: (data) => {
        return data?.status === 'completed' || data?.status === 'failed'
          ? false // Stop polling when completed or failed
          : 2000; // Poll every 2 seconds while running
      }
    }
  );
};

export const useRunPipeline = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (config: PipelineConfig) => 
      fetch('/api/pipelines/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      }).then(res => res.json()),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['pipeline', data.pipelineId]);
      }
    }
  );
};
```

## 3. UI Components

### 3.1 Pipeline Builder Interface

```jsx
// Pipeline Builder Component
const PipelineBuilder = () => {
  const { steps, addStep, removeStep, reorderSteps } = usePipelineStore();
  
  return (
    <div className="pipeline-builder">
      <div className="steps-library">
        <h3 className="text-lg font-medium">Available Steps</h3>
        <div className="grid grid-cols-2 gap-3 mt-4">
          {AVAILABLE_STEPS.map(stepType => (
            <StepCard
              key={stepType.id}
              stepType={stepType}
              onClick={() => addStep(createStep(stepType.id))}
            />
          ))}
        </div>
      </div>
      
      <div className="active-pipeline mt-8">
        <h3 className="text-lg font-medium">Current Pipeline</h3>
        <DndContext onDragEnd={handleDragEnd}>
          <SortableContext items={steps.map(s => s.id)}>
            {steps.map((step) => (
              <SortableStep
                key={step.id}
                step={step}
                onRemove={() => removeStep(step.id)}
                onConfigure={() => openStepConfig(step.id)}
              />
            ))}
          </SortableContext>
        </DndContext>
        
        {steps.length === 0 && (
          <div className="empty-pipeline">
            <p className="text-neutral-400">
              Drag steps from the library to build your pipeline
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 3.2 Step Configuration Modal

```jsx
const StepConfigModal = ({ step, isOpen, onClose, onSave }) => {
  const [config, setConfig] = useState(step.config);
  
  const handleSave = () => {
    onSave(config);
    onClose();
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <h3 className="text-xl font-semibold">{step.name} Configuration</h3>
        
        <div className="mt-4 space-y-4">
          <div className="form-group">
            <label className="block text-sm font-medium">Enable Step</label>
            <Toggle
              isOn={config.enabled}
              onChange={(enabled) => setConfig({...config, enabled})}
            />
          </div>
          
          <div className="form-group">
            <label className="block text-sm font-medium">AI Model</label>
            <Select
              value={config.params.model}
              options={AVAILABLE_MODELS}
              onChange={(model) => setConfig({
                ...config, 
                params: {...config.params, model}
              })}
            />
          </div>
          
          <div className="form-group">
            <label className="block text-sm font-medium">Prompt Template</label>
            <Textarea
              value={config.params.promptTemplate}
              onChange={(e) => setConfig({
                ...config,
                params: {...config.params, promptTemplate: e.target.value}
              })}
              className="h-32"
            />
          </div>
          
          <div className="form-group">
            <label className="block text-sm font-medium">Knowledge Documents</label>
            <KnowledgeDocSelector
              selected={config.knowledge_docs}
              onChange={(docs) => setConfig({...config, knowledge_docs: docs})}
            />
          </div>
        </div>
        
        <div className="mt-6 flex justify-end space-x-3">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>
    </Modal>
  );
};
```

### 3.3 Live Content View

```jsx
const LiveContentView = ({ pipelineId }) => {
  const { data, isLoading, error } = usePipelineRun(pipelineId);
  const [selectedStep, setSelectedStep] = useState(null);
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  const steps = data?.steps || [];
  const currentStep = selectedStep || steps[steps.length - 1]?.id;
  const stepData = data?.results?.[currentStep];
  
  return (
    <div className="live-content-view">
      <div className="step-selector">
        <StepProgress
          steps={steps}
          activeStep={currentStep}
          onStepClick={setSelectedStep}
        />
      </div>
      
      <div className="content-panel">
        {stepData ? (
          <ContentDisplay
            stepType={currentStep}
            content={stepData}
            isEdited={currentStep.includes('_edit')}
          />
        ) : (
          <EmptyState message="No content generated yet" />
        )}
      </div>
      
      {/* Controls for regeneration, editing, etc. */}
      <div className="action-panel">
        <Button 
          onClick={() => regenerateContent(currentStep)} 
          disabled={data.status === 'running'}
        >
          Regenerate
        </Button>
        <Button onClick={() => exportContent(currentStep)}>
          Export
        </Button>
      </div>
    </div>
  );
};
```

### 3.4 Editor Comparison View

```jsx
const EditorComparisonView = ({ originalContent, editedContent, feedback }) => {
  return (
    <div className="comparison-view">
      <div className="grid grid-cols-2 gap-6">
        <div className="original-content">
          <h3 className="text-lg font-medium">Original</h3>
          <div className="content-box">
            <ReactMarkdown>{originalContent}</ReactMarkdown>
          </div>
        </div>
        
        <div className="edited-content">
          <h3 className="text-lg font-medium">Edited</h3>
          <div className="content-box">
            <ReactMarkdown>{editedContent}</ReactMarkdown>
          </div>
        </div>
      </div>
      
      {feedback && (
        <div className="editor-feedback mt-6">
          <h3 className="text-lg font-medium">Editor Feedback</h3>
          <div className="feedback-box">
            <ReactMarkdown>{feedback}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};
```

## 4. Knowledge Base UI

### 4.1 Document Manager

```jsx
const KnowledgeBaseManager = () => {
  const { data: documents, isLoading } = useKnowledgeDocuments();
  const [selectedTags, setSelectedTags] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredDocs = useMemo(() => {
    return documents?.filter(doc => {
      // Filter by search term
      const matchesSearch = !searchTerm || 
        doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.content.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Filter by selected tags
      const matchesTags = selectedTags.length === 0 || 
        selectedTags.every(tag => doc.tags.includes(tag));
        
      return matchesSearch && matchesTags;
    });
  }, [documents, searchTerm, selectedTags]);
  
  return (
    <div className="knowledge-base-manager">
      <div className="search-filter-bar">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search knowledge base..."
        />
        
        <TagSelector
          availableTags={AVAILABLE_TAGS}
          selectedTags={selectedTags}
          onChange={setSelectedTags}
        />
      </div>
      
      <div className="documents-grid">
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          filteredDocs.map(doc => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onView={() => viewDocument(doc.id)}
              onEdit={() => editDocument(doc.id)}
              onDelete={() => deleteDocument(doc.id)}
            />
          ))
        )}
      </div>
      
      <Button onClick={openNewDocumentModal}>
        Add Document
      </Button>
    </div>
  );
};
```

### 4.2 Document Editor

```jsx
const DocumentEditor = ({ documentId, onSave, onCancel }) => {
  const { data: document, isLoading } = useDocument(documentId);
  const [formState, setFormState] = useState({
    name: '',
    content: '',
    doc_type: 'voice_sample',
    tags: []
  });
  
  // Load document data when available
  useEffect(() => {
    if (document) {
      setFormState({
        name: document.name,
        content: document.content,
        doc_type: document.doc_type,
        tags: document.tags
      });
    }
  }, [document]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (documentId) {
        await updateDocument(documentId, formState);
      } else {
        await createDocument(formState);
      }
      onSave();
    } catch (error) {
      console.error("Error saving document", error);
    }
  };
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <form onSubmit={handleSubmit} className="document-editor">
      <div className="form-group">
        <label>Document Name</label>
        <input
          type="text"
          value={formState.name}
          onChange={(e) => setFormState({...formState, name: e.target.value})}
          required
        />
      </div>
      
      <div className="form-group">
        <label>Document Type</label>
        <select
          value={formState.doc_type}
          onChange={(e) => setFormState({...formState, doc_type: e.target.value})}
        >
          <option value="voice_sample">Voice Sample</option>
          <option value="reference">Reference Material</option>
          <option value="instruction">Instruction</option>
          <option value="prompt_template">Prompt Template</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Content</label>
        <textarea
          value={formState.content}
          onChange={(e) => setFormState({...formState, content: e.target.value})}
          rows={12}
          required
        />
      </div>
      
      <div className="form-group">
        <label>Tags</label>
        <TagInput
          tags={formState.tags}
          onChange={(tags) => setFormState({...formState, tags})}
        />
      </div>
      
      <div className="actions">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" variant="primary">
          Save Document
        </Button>
      </div>
    </form>
  );
};
```

## 5. Page Structure

### 5.1 Layout Components

```jsx
// Main application layout
const AppLayout = ({ children }) => {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <TopNav />
        <div className="content-container">
          {children}
        </div>
      </main>
    </div>
  );
};

// Sidebar navigation
const Sidebar = () => {
  const router = useRouter();
  
  return (
    <aside className="sidebar">
      <div className="logo">
        <Logo />
      </div>
      
      <nav className="nav-links">
        <NavItem 
          href="/dashboard" 
          icon={<DashboardIcon />}
          isActive={router.pathname === '/dashboard'}
        >
          Dashboard
        </NavItem>
        
        <NavItem 
          href="/pipelines" 
          icon={<PipelinesIcon />}
          isActive={router.pathname.startsWith('/pipelines')}
        >
          Pipelines
        </NavItem>
        
        <NavItem 
          href="/knowledge-base" 
          icon={<KnowledgeIcon />}
          isActive={router.pathname.startsWith('/knowledge-base')}
        >
          Knowledge Base
        </NavItem>
        
        <NavItem 
          href="/assets" 
          icon={<AssetsIcon />}
          isActive={router.pathname.startsWith('/assets')}
        >
          Assets
        </NavItem>
        
        <NavItem 
          href="/settings" 
          icon={<SettingsIcon />}
          isActive={router.pathname.startsWith('/settings')}
        >
          Settings
        </NavItem>
      </nav>
      
      <div className="user-section">
        <UserMenu />
      </div>
    </aside>
  );
};
```

### 5.2 Main Pages

The application will include the following main pages:

1. **Dashboard**: Overview of recent pipeline runs, templates, and quick actions
2. **Pipelines**: List of saved pipelines with create/edit functionality
3. **Pipeline Builder**: Visual interface for creating and configuring pipelines
4. **Pipeline Run**: Live view of pipeline execution with results
5. **Knowledge Base**: Document management for voice samples and references
6. **Assets Library**: View and manage generated content assets
7. **Settings**: User account, API keys, and preferences

## 6. Responsive Design

The UI will be fully responsive with specific adjustments for different viewport sizes:

- **Desktop (1200px+)**: Full layout with sidebar and multi-column content
- **Tablet (768px - 1199px)**: Collapsible sidebar, simplified layout
- **Mobile (< 768px)**: Bottom navigation, stacked content, simplified controls

```css
/* Example responsive breakpoints */
@media (max-width: 1199px) {
  .app-layout {
    grid-template-columns: 64px 1fr;
  }
  
  .sidebar {
    width: 64px;
  }
  
  .sidebar .nav-text {
    display: none;
  }
}

@media (max-width: 767px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }
  
  .sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    width: 100%;
    display: flex;
    flex-direction: row;
  }
  
  .comparison-view {
    grid-template-columns: 1fr;
  }
}
```

## 7. Animations & Interactions

### 7.1 Page Transitions

```jsx
// Page transition wrapper
const PageTransition = ({ children }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
};
```

### 7.2 Pipeline Step Animations

```jsx
// Pipeline step status animation
const StepStatusIndicator = ({ status }) => {
  return (
    <motion.div
      className={`step-status status-${status}`}
      initial={false}
      animate={{
        scale: status === 'running' ? [1, 1.1, 1] : 1,
        backgroundColor: {
          pending: 'var(--neutral-500)',
          running: 'var(--info)',
          completed: 'var(--success)',
          failed: 'var(--error)'
        }[status]
      }}
      transition={{
        scale: {
          repeat: status === 'running' ? Infinity : 0,
          duration: 1.5
        }
      }}
    />
  );
};
```

### 7.3 Content Reveal

```jsx
// Content reveal animation
const RevealContent = ({ content }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: 'auto', opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="content-box"
      >
        {content}
      </motion.div>
    </motion.div>
  );
};
```

## 8. Implementation Timeline

The UI Modernization phase is estimated to take 4-6 weeks with the following timeline:

### Weeks 1-2: Foundation & Components
- Set up Next.js project structure
- Implement design system and basic components
- Create layout and navigation structure

### Weeks 3-4: Core Functionality
- Build pipeline builder interface
- Implement knowledge base management
- Create content viewing components

### Weeks 5-6: Polish & Integration
- Add animations and microinteractions
- Implement responsive design
- Connect to API endpoints
- Testing and optimization

## 9. Dependencies

### Development Dependencies
- Next.js v13+
- React v18+
- TypeScript v4.8+
- Tailwind CSS v3.2+
- Framer Motion v7+
- Zustand v4+
- React Query v4+
- React Hook Form v7+
- date-fns v2.29+
- React Icons v4+

### Design Dependencies
- Figma (UI design)
- Inter font family
- JetBrains Mono font family
- Custom icon set

## 10. Next Steps

1. Create wireframes in Figma for key screens
2. Define component API contracts
3. Set up Next.js project with Tailwind configuration
4. Develop core components in Storybook
5. Implement main page layouts
6. Create integration points with backend API 