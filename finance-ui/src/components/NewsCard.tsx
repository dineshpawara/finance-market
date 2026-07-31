import React from 'react';
import { Newspaper, ExternalLink, ArrowUpRight, ArrowDownRight, Minus, RefreshCw } from 'lucide-react';
import type { NewsItem } from '../utils/mockMarketData';
import { getTimeAgo } from '../utils/formatters';
import { GROWW_THEME } from '../utils/theme';

interface NewsCardProps {
  newsItems: NewsItem[];
  sentiment: { score: number; label: string; count: number };
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const NewsCard: React.FC<NewsCardProps> = ({
  newsItems,
  sentiment,
  onRefresh,
  isRefreshing = false,
}) => {
  const isBullishSentiment = sentiment.label === 'BULLISH';
  const isBearishSentiment = sentiment.label === 'BEARISH';

  return (
    <div className="groww-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="groww-card-header" style={{ marginBottom: '12px' }}>
        <div className="groww-card-title">
          <Newspaper size={20} color={GROWW_THEME.colors.green} />
          <span>Top Market News</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Manual Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh RSS Feeds & Re-classify"
              style={{
                background: 'transparent',
                border: `1px solid ${GROWW_THEME.colors.border}`,
                borderRadius: '6px',
                padding: '4px 8px',
                cursor: 'pointer',
                color: GROWW_THEME.colors.textSecondary,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.75rem',
              }}
            >
              <RefreshCw size={12} className={isRefreshing ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          )}

          {/* Overall Sentiment Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '4px 10px',
              borderRadius: '20px',
              backgroundColor: isBullishSentiment
                ? GROWW_THEME.colors.greenBg
                : isBearishSentiment
                  ? GROWW_THEME.colors.redBg
                  : GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${isBullishSentiment
                  ? GROWW_THEME.colors.greenBorder
                  : isBearishSentiment
                    ? GROWW_THEME.colors.redBorder
                    : GROWW_THEME.colors.border
                }`,
              color: isBullishSentiment
                ? GROWW_THEME.colors.green
                : isBearishSentiment
                  ? GROWW_THEME.colors.red
                  : GROWW_THEME.colors.textSecondary,
            }}
          >
            <span>SENTIMENT:</span>
            <span>{sentiment.label} ({sentiment.score}%)</span>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
        {newsItems.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: GROWW_THEME.colors.textMuted, fontSize: '0.85rem' }}>
            No news articles available. Click refresh to fetch latest feeds.
          </div>
        ) : (
          newsItems.map(item => {
            const isBullish = item.sentiment === 'BULLISH';
            const isBearish = item.sentiment === 'BEARISH';
            const confidencePercent = item.score ? Math.round(item.score * 100) : null;

            return (
              <div
                key={item.id}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                  border: `1px solid ${GROWW_THEME.colors.border}`,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
                  <a
                    href={item.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ textDecoration: 'none', color: GROWW_THEME.colors.textPrimary, flex: 1 }}
                  >
                    <h4 style={{ fontSize: '0.88rem', fontWeight: 600, lineHeight: 1.35, color: GROWW_THEME.colors.textPrimary }}>
                      {item.title}
                    </h4>
                  </a>
                  {item.link && item.link !== '#' && (
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Open full news article"
                      style={{ color: GROWW_THEME.colors.textMuted, textDecoration: 'none' }}
                    >
                      <ExternalLink size={14} style={{ flexShrink: 0, cursor: 'pointer' }} />
                    </a>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', fontSize: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: GROWW_THEME.colors.textMuted, fontWeight: 500 }}>{item.source}</span>
                    <span style={{ color: GROWW_THEME.colors.border }}>•</span>
                    <span style={{ color: GROWW_THEME.colors.textMuted }}>{getTimeAgo(item.time)}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {confidencePercent && (
                      <span style={{ fontSize: '0.68rem', color: GROWW_THEME.colors.textMuted }}>
                        FinBERT: {confidencePercent}%
                      </span>
                    )}

                    <div
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: isBullish
                          ? GROWW_THEME.colors.greenBg
                          : isBearish
                            ? GROWW_THEME.colors.redBg
                            : GROWW_THEME.colors.bgSurfaceHover,
                        color: isBullish
                          ? GROWW_THEME.colors.green
                          : isBearish
                            ? GROWW_THEME.colors.red
                            : GROWW_THEME.colors.textSecondary,
                      }}
                    >
                      {isBullish ? <ArrowUpRight size={12} /> : isBearish ? <ArrowDownRight size={12} /> : <Minus size={12} />}
                      <span>{item.sentiment}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
