import React from 'react';
import type { OptionChainSummary } from '../utils/mockMarketData';
import { formatNumber } from '../utils/formatters';
import { GROWW_THEME } from '../utils/theme';
import { Layers } from 'lucide-react';

interface OptionChainTableProps {
  data: OptionChainSummary | null;
  selectedExpiry: string;
  onExpiryChange: (expiry: string) => void;
  underlying: string;
  onUnderlyingChange: (symbol: string) => void;
  availableIndices: string[];
}

export const OptionChainTable: React.FC<OptionChainTableProps> = ({
  data,
  selectedExpiry,
  onExpiryChange,
  underlying,
  onUnderlyingChange,
  availableIndices,
}) => {
  if (!data) return <div style={{ color: GROWW_THEME.colors.textMuted }}>Loading Option Chain data...</div>;

  const atmStrike = Math.round(data.underlyingPrice / 50) * 50;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div className="groww-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers color={GROWW_THEME.colors.green} size={22} />
            <h2 style={{ fontSize: '1.2rem' }}>Option Chain Matrix</h2>
          </div>

          <select
            value={underlying}
            onChange={(e) => onUnderlyingChange(e.target.value)}
            className="groww-select"
            style={{ fontWeight: 700 }}
          >
            {availableIndices.map(idx => (
              <option key={idx} value={idx}>{idx}</option>
            ))}
          </select>

          <select
            value={selectedExpiry}
            onChange={(e) => onExpiryChange(e.target.value)}
            className="groww-select"
          >
            {data.expiryDates.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Metrics Summary */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>LTP</span>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: GROWW_THEME.colors.green }}>
              {formatNumber(data.underlyingPrice)}
            </div>
          </div>

          <div style={{ height: '30px', width: '1px', backgroundColor: GROWW_THEME.colors.border }} />

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>PCR (Put Call Ratio)</span>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: data.pcr > 1 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
              {data.pcr} ({data.pcr > 1 ? 'Bullish' : 'Bearish'})
            </div>
          </div>

          <div style={{ height: '30px', width: '1px', backgroundColor: GROWW_THEME.colors.border }} />

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>Max Pain</span>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: GROWW_THEME.colors.yellow }}>
              {data.maxPain}
            </div>
          </div>
        </div>
      </div>

      {/* Option Chain Table */}
      <div className="groww-table-wrapper">
        <table className="groww-table">
          <thead>
            <tr>
              <th colSpan={4} style={{ textAlign: 'center', background: 'rgba(0, 208, 156, 0.08)', color: GROWW_THEME.colors.green, borderRight: `1px solid ${GROWW_THEME.colors.border}` }}>
                CALLS (CE)
              </th>
              <th style={{ textAlign: 'center', background: GROWW_THEME.colors.bgSurfaceHover, color: GROWW_THEME.colors.textPrimary }}>
                STRIKE
              </th>
              <th colSpan={4} style={{ textAlign: 'center', background: 'rgba(235, 87, 87, 0.08)', color: GROWW_THEME.colors.red, borderLeft: `1px solid ${GROWW_THEME.colors.border}` }}>
                PUTS (PE)
              </th>
            </tr>
            <tr>
              <th style={{ textAlign: 'right' }}>OI (Lakhs)</th>
              <th style={{ textAlign: 'right' }}>Chg in OI</th>
              <th style={{ textAlign: 'right' }}>IV (%)</th>
              <th style={{ textAlign: 'right', borderRight: `1px solid ${GROWW_THEME.colors.border}` }}>LTP (₹)</th>
              <th style={{ textAlign: 'center', fontWeight: 800 }}>STRIKE PRICE</th>
              <th style={{ textAlign: 'left', borderLeft: `1px solid ${GROWW_THEME.colors.border}` }}>LTP (₹)</th>
              <th style={{ textAlign: 'left' }}>IV (%)</th>
              <th style={{ textAlign: 'left' }}>Chg in OI</th>
              <th style={{ textAlign: 'left' }}>OI (Lakhs)</th>
            </tr>
          </thead>
          <tbody>
            {data.strikes.map((s) => {
              const isATM = s.strike === atmStrike;
              const isCallITM = s.strike < data.underlyingPrice;
              const isPutITM = s.strike > data.underlyingPrice;

              return (
                <tr
                  key={s.strike}
                  style={{
                    backgroundColor: isATM
                      ? 'rgba(255, 183, 3, 0.15)'
                      : undefined,
                  }}
                >
                  {/* Calls Side */}
                  <td style={{ textAlign: 'right', backgroundColor: isCallITM ? 'rgba(0, 208, 156, 0.04)' : undefined, fontFamily: 'JetBrains Mono' }}>
                    {formatNumber(s.callOI / 100, 1)}
                  </td>
                  <td style={{ textAlign: 'right', backgroundColor: isCallITM ? 'rgba(0, 208, 156, 0.04)' : undefined, fontFamily: 'JetBrains Mono', color: s.callChgOI >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                    {s.callChgOI > 0 ? `+${s.callChgOI}` : s.callChgOI}
                  </td>
                  <td style={{ textAlign: 'right', backgroundColor: isCallITM ? 'rgba(0, 208, 156, 0.04)' : undefined, fontFamily: 'JetBrains Mono', color: GROWW_THEME.colors.textMuted }}>
                    {s.callIv}
                  </td>
                  <td style={{ textAlign: 'right', backgroundColor: isCallITM ? 'rgba(0, 208, 156, 0.04)' : undefined, fontFamily: 'JetBrains Mono', fontWeight: 700, color: GROWW_THEME.colors.green, borderRight: `1px solid ${GROWW_THEME.colors.border}` }}>
                    {s.callLtp}
                  </td>

                  {/* Strike Price */}
                  <td
                    style={{
                      textAlign: 'center',
                      fontWeight: isATM ? 900 : 700,
                      fontFamily: 'JetBrains Mono',
                      fontSize: isATM ? '1.02rem' : '0.9rem',
                      color: isATM ? GROWW_THEME.colors.yellow : GROWW_THEME.colors.textPrimary,
                      background: isATM ? 'rgba(255, 183, 3, 0.25)' : GROWW_THEME.colors.bgSurfaceHover,
                    }}
                  >
                    {s.strike} {isATM ? '(ATM)' : ''}
                  </td>

                  {/* Puts Side */}
                  <td style={{ textAlign: 'left', backgroundColor: isPutITM ? 'rgba(235, 87, 87, 0.04)' : undefined, fontFamily: 'JetBrains Mono', fontWeight: 700, color: GROWW_THEME.colors.red, borderLeft: `1px solid ${GROWW_THEME.colors.border}` }}>
                    {s.putLtp}
                  </td>
                  <td style={{ textAlign: 'left', backgroundColor: isPutITM ? 'rgba(235, 87, 87, 0.04)' : undefined, fontFamily: 'JetBrains Mono', color: GROWW_THEME.colors.textMuted }}>
                    {s.putIv}
                  </td>
                  <td style={{ textAlign: 'left', backgroundColor: isPutITM ? 'rgba(235, 87, 87, 0.04)' : undefined, fontFamily: 'JetBrains Mono', color: s.putChgOI >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                    {s.putChgOI > 0 ? `+${s.putChgOI}` : s.putChgOI}
                  </td>
                  <td style={{ textAlign: 'left', backgroundColor: isPutITM ? 'rgba(235, 87, 87, 0.04)' : undefined, fontFamily: 'JetBrains Mono' }}>
                    {formatNumber(s.putOI / 100, 1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
