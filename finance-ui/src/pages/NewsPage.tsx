import React from 'react';
import { useNewsController } from '../controller/newsController';
import { GROWW_THEME } from '../utils/theme';
import { ArrowUpRight, ArrowDownRight, Minus, Filter, ExternalLink, RefreshCw } from 'lucide-react';
import { getTimeAgo } from '../utils/formatters';

export const NewsPage: React.FC = () => {
  const { filterSentiment, handleSentimentFilter, filteredNews, loading, refresh, isRefreshing } = useNewsController();

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Market News & Sentiment</h1>
          <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textMuted }}>
            Live RSS feeds with Hugging Face FinBERT sentiment analysis & real-world market articles
          </p>
        </div>

        {/* Sentiment Filter Tabs & Refresh Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={refresh}
            disabled={isRefreshing}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: `1px solid ${GROWW_THEME.colors.border}`,
              backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
              color: GROWW_THEME.colors.textSecondary,
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            <span>{isRefreshing ? 'Refreshing Feeds...' : 'Refresh RSS'}</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color={GROWW_THEME.colors.textMuted} />
            {(['ALL', 'BULLISH', 'BEARISH', 'NEUTRAL'] as const).map(s => (
              <button
                key={s}
                onClick={() => handleSentimentFilter(s)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  border: `1px solid ${filterSentiment === s ? GROWW_THEME.colors.greenBorder : GROWW_THEME.colors.border}`,
                  backgroundColor: filterSentiment === s ? GROWW_THEME.colors.greenBg : GROWW_THEME.colors.bgSurfaceHover,
                  color: filterSentiment === s ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {loading ? (
          <div style={{ color: GROWW_THEME.colors.textMuted, padding: '30px', textAlign: 'center' }}>Loading live RSS news feed...</div>
        ) : filteredNews.length === 0 ? (
          <div style={{ color: GROWW_THEME.colors.textMuted, padding: '30px', textAlign: 'center' }}>
            No articles match the selected filter. Try selecting 'ALL' or clicking 'Refresh RSS'.
          </div>
        ) : (
          filteredNews.map(item => {
            const isBullish = item.sentiment === 'BULLISH';
            const isBearish = item.sentiment === 'BEARISH';

            return (
              <div
                key={item.id}
                className="groww-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: GROWW_THEME.colors.blue, textTransform: 'uppercase' }}>
                      {item.category}
                    </span>
                    <a
                      href={item.link || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ textDecoration: 'none', color: GROWW_THEME.colors.textPrimary }}
                    >
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '4px', lineHeight: 1.4, display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{item.title}</span>
                        {item.link && item.link !== '#' && <ExternalLink size={15} style={{ color: GROWW_THEME.colors.textMuted, flexShrink: 0 }} />}
                      </h3>
                    </a>
                  </div>

                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      backgroundColor: isBullish ? GROWW_THEME.colors.greenBg : isBearish ? GROWW_THEME.colors.redBg : GROWW_THEME.colors.bgSurfaceHover,
                      color: isBullish ? GROWW_THEME.colors.green : isBearish ? GROWW_THEME.colors.red : GROWW_THEME.colors.textSecondary,
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {isBullish ? <ArrowUpRight size={14} /> : isBearish ? <ArrowDownRight size={14} /> : <Minus size={14} />}
                    <span>{item.sentiment} ({(item.score * 100).toFixed(0)}%)</span>
                  </div>
                </div>

                <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textSecondary, lineHeight: 1.5 }}>
                  {item.summary}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: `1px solid ${GROWW_THEME.colors.borderSubtle}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: GROWW_THEME.colors.textMuted }}>
                      {item.source}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: GROWW_THEME.colors.textMuted }}>
                      {getTimeAgo(item.time)}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>Impact:</span>
                    {item.impactedStocks.map(st => (
                      <span key={st} className="mono" style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: GROWW_THEME.colors.bgSurfaceHover, color: GROWW_THEME.colors.green, fontWeight: 700 }}>
                        {st}
                      </span>
                    ))}
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

