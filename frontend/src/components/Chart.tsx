import React, { useRef, useEffect, useState } from "react";
import {
  createChart,
  ColorType,
  IChartApi,
  UTCTimestamp,
  ISeriesApi,
  SeriesMarker,
  BarData,
} from "lightweight-charts";
import axios from "axios";

interface Trade {
  side: "BUY" | "SELL";
  price: number;
  size: number;
  timestamp: string; // YYYY-MM-DD
  reason: string;
}

interface OHLC {
  timestamp: string; // YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;
}

interface ChartProps {
  symbol: string;
}

const Chart: React.FC<ChartProps> = ({ symbol }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [ohlcData, setOhlcData] = useState<OHLC[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);

  // Fetch OHLC + trades
  useEffect(() => {
    async function fetchData() {
      try {
        const ohlcRes = await axios.get<OHLC[]>(`http://localhost:8000/backtests/1/ohlc?symbol=${symbol}`);
        const tradesRes = await axios.get<Trade[]>(`http://localhost:8000/backtests/1/trades`);
        setOhlcData(ohlcRes.data);
        setTrades(tradesRes.data);
      } catch (err) {
        console.error(err);
      }
    }
    fetchData();
  }, [symbol]);

  // Create and update chart
  useEffect(() => {
    if (!chartContainerRef.current || ohlcData.length === 0) return;

    const chart: IChartApi = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: "#1e1e2f" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "#2a2a3f" },
        horzLines: { color: "#2a2a3f" },
      },
      rightPriceScale: {
        borderColor: "#44475a",
      },
      timeScale: {
        borderColor: "#44475a",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1, // magnet crosshair
      },
    });

    const candleSeries: ISeriesApi<"Candlestick"> = chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: true,
      borderColor: "#000000",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    // Deduplicate and format OHLC data
    const uniqueOhlcMap = new Map<number, BarData>();
    ohlcData.forEach(d => {
      const timestamp = Math.floor(new Date(d.timestamp).getTime() / 1000);
      if (!isNaN(timestamp)) {
        uniqueOhlcMap.set(timestamp, {
          time: timestamp as UTCTimestamp,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        });
      }
    });

    const cleanedOhlc = Array.from(uniqueOhlcMap.values()).sort(
        (a, b) => Number(a.time) - Number(b.time)
      );
    candleSeries.setData(cleanedOhlc);

    // Add trade markers
    const markers: SeriesMarker<UTCTimestamp>[] = trades.map(trade => ({
      time: Math.floor(new Date(trade.timestamp).getTime() / 1000) as UTCTimestamp,
      position: trade.side === "BUY" ? "belowBar" : "aboveBar",
      color: trade.side === "BUY" ? "#00ff7f" : "#ff4500",
      shape: trade.side === "BUY" ? "arrowUp" : "arrowDown",
      text: trade.side,
    }));
    candleSeries.setMarkers(markers);

    // Tooltip setup
    const toolTip = document.createElement("div");
    toolTip.style.position = "absolute";
    toolTip.style.display = "none";
    toolTip.style.background = "#2c2c3c";
    toolTip.style.color = "#fff";
    toolTip.style.padding = "5px 10px";
    toolTip.style.borderRadius = "4px";
    toolTip.style.pointerEvents = "none";
    toolTip.style.fontSize = "12px";
    toolTip.style.zIndex = "10";
    chartContainerRef.current.appendChild(toolTip);

    chart.subscribeCrosshairMove(param => {
      if (!param || !param.time || !param.seriesData.size || !param.point) {
        toolTip.style.display = "none";
        return;
      }

      const ohlc = param.seriesData.get(candleSeries) as BarData;
      if (!ohlc) return;

      toolTip.style.display = "block";
      const { x, y } = param.point;
      toolTip.style.left = x + 10 + "px";
      toolTip.style.top = y + 10 + "px";
      toolTip.innerHTML = `
        <div>O: ${ohlc.open}</div>
        <div>H: ${ohlc.high}</div>
        <div>L: ${ohlc.low}</div>
        <div>C: ${ohlc.close}</div>
      `;
    });

    // Resize handler
    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current!.clientWidth });
    };
    window.addEventListener("resize", handleResize);

    return () => {
      chart.remove();
      window.removeEventListener("resize", handleResize);
      if (toolTip) toolTip.remove();
    };
  }, [ohlcData, trades]);

  return <div ref={chartContainerRef} style={{ width: "100%", height: "500px", position: "relative" }} />;
};

export default Chart;
