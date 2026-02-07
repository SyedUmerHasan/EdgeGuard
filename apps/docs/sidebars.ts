import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'installation',
    'configuration',
    'usage',
    'architecture',
    {
      type: 'category',
      label: 'Features',
      link: {
        type: 'doc',
        id: 'features/index',
      },
      items: [
        'features/device-discovery',
        'features/traffic-analysis',
        'features/threat-detection',
        'features/ai-analysis',
        'features/response-system',
        'features/user-dashboard',
        'features/vulnerability-management',
        'features/network-segmentation',
        'features/threat-intelligence',
      ],
    },
    {
      type: 'category',
      label: 'Project Plan',
      link: {
        type: 'doc',
        id: 'project-plan/index',
      },
      items: [
        'project-plan/overview/project-overview',
        'project-plan/government-validation/federal-priorities',
        'project-plan/research-foundation/overview',
        {
          type: 'category',
          label: 'Development Roadmap',
          items: [
            'project-plan/implementation/phase-1-foundation',
            'project-plan/implementation/phase-2-advanced',
            'project-plan/implementation/phase-3-intelligence',
          ],
        },
        'project-plan/innovation/unique-contributions',
      ],
    },
  ],
};

export default sidebars;
