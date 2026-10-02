import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Position {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  qty: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  timestamp: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  qty: number;
  price: number;
  type: 'MARKET' | 'LIMIT';
  status: 'EXECUTED' | 'PENDING' | 'CANCELLED';
  timestamp: string;
}

interface PaperTradingContextType {
  balance: number;
  availableMargin: number;
  usedMargin: number;
  totalPnl: number;
  positions: Position[];
  orders: Order[];
  placeOrder: (symbol: string, side: 'BUY' | 'SELL', qty: number, price: number, type?: 'MARKET' | 'LIMIT') => void;
  closePosition: (positionId: string, currentPrice?: number) => void;
  updateLivePrices: (priceMap: Record<string, number>) => void;
  resetAccount: () => void;
}

const INITIAL_BALANCE = 1000000; // 10 Lakhs INR Paper Trading Capital
const STORAGE_KEY = 'groww_paper_trading';

const PaperTradingContext = createContext<PaperTradingContextType | undefined>(undefined);

export const PaperTradingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [balance, setBalance] = useState<number>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.balance ?? INITIAL_BALANCE;
      } catch {
        return INITIAL_BALANCE;
      }
    }
    return INITIAL_BALANCE;
  });

  const [positions, setPositions] = useState<Position[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.positions ?? [];
      } catch {
        return [];
      }
    }
    return [];
  });

  const [orders, setOrders] = useState<Order[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.orders ?? [];
      } catch {
        return [];
      }
    }
    return [];
  });

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ balance, positions, orders })
    );
  }, [balance, positions, orders]);

  // Calculate used margin based on open positions
  const usedMargin = positions.reduce((acc, pos) => acc + pos.qty * pos.entryPrice, 0);
  const totalPnl = positions.reduce((acc, pos) => acc + pos.pnl, 0);
  const availableMargin = balance - usedMargin + totalPnl;

  const placeOrder = (
    symbol: string,
    side: 'BUY' | 'SELL',
    qty: number,
    price: number,
    type: 'MARKET' | 'LIMIT' = 'MARKET'
  ) => {
    const requiredMargin = qty * price;
    if (requiredMargin > availableMargin && side === 'BUY') {
      alert(`Insufficient Available Margin! Required: ₹${requiredMargin.toFixed(2)}, Available: ₹${availableMargin.toFixed(2)}`);
      return;
    }

    const now = new Date().toLocaleTimeString();
    const newOrder: Order = {
      id: `ORD-${Date.now().toString().slice(-6)}`,
      symbol,
      side,
      qty,
      price,
      type,
      status: 'EXECUTED',
      timestamp: now,
    };

    setOrders(prev => [newOrder, ...prev]);

    // Check if an open position exists for the symbol
    const existingIndex = positions.findIndex(p => p.symbol === symbol && p.side === side);
    if (existingIndex >= 0) {
      const existing = positions[existingIndex];
      const newQty = existing.qty + qty;
      const avgPrice = (existing.qty * existing.entryPrice + qty * price) / newQty;
      const updatedPositions = [...positions];
      updatedPositions[existingIndex] = {
        ...existing,
        qty: newQty,
        entryPrice: avgPrice,
        currentPrice: price,
        pnl: side === 'BUY' ? (price - avgPrice) * newQty : (avgPrice - price) * newQty,
        pnlPercent: side === 'BUY' ? ((price - avgPrice) / avgPrice) * 100 : ((avgPrice - price) / avgPrice) * 100,
      };
      setPositions(updatedPositions);
    } else {
      const newPosition: Position = {
        id: `POS-${Date.now().toString().slice(-6)}`,
        symbol,
        side,
        qty,
        entryPrice: price,
        currentPrice: price,
        pnl: 0,
        pnlPercent: 0,
        timestamp: now,
      };
      setPositions(prev => [newPosition, ...prev]);
    }
  };

  const closePosition = (positionId: string, customPrice?: number) => {
    const target = positions.find(p => p.id === positionId);
    if (!target) return;

    const exitPrice = customPrice ?? target.currentPrice;
    const realizedPnl = target.side === 'BUY'
      ? (exitPrice - target.entryPrice) * target.qty
      : (target.entryPrice - exitPrice) * target.qty;

    setBalance(prev => prev + realizedPnl);

    const now = new Date().toLocaleTimeString();
    const closeOrder: Order = {
      id: `ORD-CLOSE-${Date.now().toString().slice(-6)}`,
      symbol: target.symbol,
      side: target.side === 'BUY' ? 'SELL' : 'BUY',
      qty: target.qty,
      price: exitPrice,
      type: 'MARKET',
      status: 'EXECUTED',
      timestamp: now,
    };

    setOrders(prev => [closeOrder, ...prev]);
    setPositions(prev => prev.filter(p => p.id !== positionId));
  };

  const updateLivePrices = (priceMap: Record<string, number>) => {
    setPositions(prev =>
      prev.map(pos => {
        const live = priceMap[pos.symbol];
        if (!live) return pos;
        const pnl = pos.side === 'BUY'
          ? (live - pos.entryPrice) * pos.qty
          : (pos.entryPrice - live) * pos.qty;
        const pnlPercent = pos.side === 'BUY'
          ? ((live - pos.entryPrice) / pos.entryPrice) * 100
          : ((pos.entryPrice - live) / pos.entryPrice) * 100;
        return {
          ...pos,
          currentPrice: live,
          pnl,
          pnlPercent,
        };
      })
    );
  };

  const resetAccount = () => {
    setBalance(INITIAL_BALANCE);
    setPositions([]);
    setOrders([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <PaperTradingContext.Provider
      value={{
        balance,
        availableMargin,
        usedMargin,
        totalPnl,
        positions,
        orders,
        placeOrder,
        closePosition,
        updateLivePrices,
        resetAccount,
      }}
    >
      {children}
    </PaperTradingContext.Provider>
  );
};

export const usePaperTrading = (): PaperTradingContextType => {
  const context = useContext(PaperTradingContext);
  if (!context) {
    throw new Error('usePaperTrading must be used within a PaperTradingProvider');
  }
  return context;
};
