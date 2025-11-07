// This is a placeholder file to resolve dependencies from the copied editor app.
// The actual state management logic is not implemented for this demo.

export type SidebarMode = 'concepts' | 'inferences' | 'json' | 'repositories';

export const useStore = () => {
  return {
    repositorySet: {
      name: 'Demo',
      concepts: [],
      inferences: [],
    },
    loadRepositorySet: (name: string) => console.log(`Attempted to load ${name}`),
  };
};
