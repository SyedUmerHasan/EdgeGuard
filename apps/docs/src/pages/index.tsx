import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  const logoUrl = useBaseUrl('img/logo.svg');
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <div className={styles.heroContent}>
          <div className={styles.heroText}>
            <div className={styles.heroLogoInline}>
              <img src={logoUrl} alt="EdgeGuard Logo" width="60" height="60" />
              <Heading as="h1" className={styles.heroTitle}>
                EdgeGuard
              </Heading>
            </div>
            <p className={styles.heroSubtitle}>
              AI-Powered IoT Security for Home Networks
            </p>
            <p className={styles.heroDescription}>
              Privacy-first threat detection using local AI. Protect your smart home 
              with enterprise-grade security that runs entirely on your device.
            </p>
            <div className={styles.buttons}>
              <Link
                className="button button--secondary button--lg"
                to="docs/intro">
                Get Started →
              </Link>
              <a
                className={`button button--lg ${styles.githubButton}`}
                href="https://github.com/SyedUmerHasan/EdgeGuard">
                GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - AI-Powered IoT Security`}
      description="Privacy-first IoT threat detection using local AI for home networks">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        
        {/* Quick Start Section */}
        <section style={{padding: '4rem 0', background: '#f8fafc'}}>
          <div className="container">
            <div className="row">
              <div className="col col--6">
                <h2 style={{fontSize: '2.5rem', marginBottom: '1rem'}}>Get Started in Minutes</h2>
                <p style={{fontSize: '1.1rem', color: '#64748b', marginBottom: '2rem'}}>
                  EdgeGuard is designed for easy deployment on any Linux system. 
                  No complex configuration required.
                </p>
                <pre style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1rem', color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.95rem', lineHeight: '1.8', overflow: 'auto'}}>
git clone https://github.com/SyedUmerHasan/EdgeGuard.git{'\n'}cd EdgeGuard{'\n'}pip install -r requirements.txt{'\n'}sudo python3 main.py
                </pre>
                <Link
                  className="button button--primary button--lg"
                  to="docs/installation">
                  View Full Installation Guide →
                </Link>
              </div>
              <div className="col col--6">
                <div style={{background: 'white', padding: '2rem', borderRadius: '1rem', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}}>
                  <h3 style={{marginBottom: '1.5rem', color: '#1e293b'}}>System Requirements</h3>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <span style={{color: '#10b981', fontSize: '1.25rem', fontWeight: 'bold'}}>✓</span>
                      <span style={{color: '#64748b'}}>Python 3.8+</span>
                    </div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <span style={{color: '#10b981', fontSize: '1.25rem', fontWeight: 'bold'}}>✓</span>
                      <span style={{color: '#64748b'}}>Linux / macOS / WSL</span>
                    </div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <span style={{color: '#10b981', fontSize: '1.25rem', fontWeight: 'bold'}}>✓</span>
                      <span style={{color: '#64748b'}}>2GB RAM minimum</span>
                    </div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <span style={{color: '#10b981', fontSize: '1.25rem', fontWeight: 'bold'}}>✓</span>
                      <span style={{color: '#64748b'}}>Ollama with Llama 3.2</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section style={{padding: '4rem 0', background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)', color: 'white'}}>
          <div className="container">
            <div className="row">
              <div className="col col--3 text--center">
                <h3 style={{fontSize: '3rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>99%+</h3>
                <p style={{fontSize: '1.1rem', opacity: 0.9}}>Threat Detection Accuracy</p>
              </div>
              <div className="col col--3 text--center">
                <h3 style={{fontSize: '3rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>100%</h3>
                <p style={{fontSize: '1.1rem', opacity: 0.9}}>Local Processing</p>
              </div>
              <div className="col col--3 text--center">
                <h3 style={{fontSize: '3rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>24/7</h3>
                <p style={{fontSize: '1.1rem', opacity: 0.9}}>Network Monitoring</p>
              </div>
              <div className="col col--3 text--center">
                <h3 style={{fontSize: '3rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>MIT</h3>
                <p style={{fontSize: '1.1rem', opacity: 0.9}}>Open Source License</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section style={{padding: '5rem 0', textAlign: 'center'}}>
          <div className="container">
            <h2 style={{fontSize: '2.5rem', marginBottom: '1rem'}}>Ready to Secure Your Network?</h2>
            <p style={{fontSize: '1.2rem', color: '#64748b', marginBottom: '2rem'}}>
              Join the community protecting home networks with AI-powered security
            </p>
            <div style={{display: 'flex', gap: '1rem', justifyContent: 'center'}}>
              <Link
                className="button button--primary button--lg"
                to="docs/intro">
                Get Started
              </Link>
              <a
                className="button button--secondary button--lg"
                href="https://github.com/SyedUmerHasan/EdgeGuard">
                View on GitHub
              </a>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
