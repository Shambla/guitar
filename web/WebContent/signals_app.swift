import SwiftUI

struct SignalsAppView: View {
    @StateObject private var viewModel = SignalsViewModel()
    @State private var isPro = false
    @State private var selectedFilter: Filter = .all
    @State private var showCodeExplanation = false

    var filteredSignals: [Signal] {
        let base = viewModel.signals.isEmpty ? Signal.sample : viewModel.signals
        switch selectedFilter {
        case .all:
            return base
        case .crypto:
            return base.filter { $0.category == .crypto }
        case .stocks:
            return base.filter { $0.category == .stocks }
        }
    }

    var cryptoSignals: [Signal] {
        filteredSignals.filter { $0.category == .crypto }
    }

    var stockSignals: [Signal] {
        filteredSignals.filter { $0.category == .stocks }
    }

    var body: some View {
        ZStack {
            SynthwaveBackground()
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 16) {
                        HeaderBar(isPro: $isPro)
                        PriceHero()
                        QuickNavigation { section in
                            withAnimation(.easeInOut(duration: 0.25)) {
                                proxy.scrollTo(section, anchor: .top)
                            }
                        }
                        FilterPills(selected: $selectedFilter)
                        StatusChip(text: viewModel.statusText, isActive: viewModel.isConnected)

                        LiveSignalsSection(cryptoSignals: cryptoSignals, stockSignals: stockSignals, selectedFilter: selectedFilter)
                            .id(SectionAnchor.liveSignals)

                        BitcoinDominanceSection(value: viewModel.bitcoinDominance)
                            .id(SectionAnchor.bitcoinDominance)

                        TopSignalsSection(signals: filteredSignals)
                            .id(SectionAnchor.topSignals)

                        HistoricalSignalsSection(
                            historicalCrypto: viewModel.historicalCryptoSignals,
                            historicalStock: viewModel.historicalStockSignals
                        )
                            .id(SectionAnchor.historicalSignals)

                        WatchlistSection()
                            .id(SectionAnchor.watchlist)

                        MarketBreadthSection()
                            .id(SectionAnchor.marketBreadth)

                        AssetsTradedSection()
                            .id(SectionAnchor.assetsTraded)

                        UpgradeCTA()
                            .id(SectionAnchor.upgrade)
                    }
                    .padding(.horizontal, 18)
                    .padding(.top, 16)
                }
            }
        }
        .task {
            await viewModel.start()
        }
    }
}

struct HeaderBar: View {
    @Binding var isPro: Bool

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Text("Trading Signals")
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                Text("Live Feed • Mac iOS App Store")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.8))
            }
            Spacer()
            Toggle(isOn: $isPro) {
                Text("PRO")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
            }
            .labelsHidden()
            .toggleStyle(NeonToggleStyle())
        }
        .padding(14)
        .background(.ultraThinMaterial.opacity(0.75))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.cyan.opacity(0.5), lineWidth: 1)
        )
    }
}

struct PriceHero: View {
    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 8) {
                Text("ROI")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color.white.opacity(0.7))
                Text("+284.6%")
                    .font(.system(size: 30, weight: .heavy, design: .rounded))
                    .foregroundStyle(LinearGradient(
                        colors: [.pink, .orange, .yellow, .green, .cyan, .pink],
                        startPoint: .leading,
                        endPoint: .trailing
                    ))
                Text("Updated 2m ago • Auto ML signals")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.7))
            }
            Spacer()
            ZStack {
                Circle()
                    .fill(Color.yellow.opacity(0.2))
                    .frame(width: 86, height: 86)
                    .overlay(
                        Circle().stroke(Color.yellow.opacity(0.6), lineWidth: 2)
                    )
                Text("🚀")
                    .font(.system(size: 36))
            }
        }
        .padding(16)
        .background(Color.black.opacity(0.35))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.pink.opacity(0.5), lineWidth: 1)
        )
    }
}

struct FilterPills: View {
    @Binding var selected: Filter

    var body: some View {
        HStack(spacing: 10) {
            ForEach(Filter.allCases, id: \.self) { filter in
                Button(action: { selected = filter }) {
                    Text(filter.title)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(selected == filter ? .black : .white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            Capsule().fill(selected == filter ? Color.cyan : Color.white.opacity(0.12))
                        )
                        .overlay(
                            Capsule().stroke(Color.cyan.opacity(0.4), lineWidth: 1)
                        )
                }
            }
        }
    }
}

struct StatusChip: View {
    let text: String
    let isActive: Bool

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isActive ? Color.green : Color.orange)
                .frame(width: 8, height: 8)
            Text(text)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.white)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.black.opacity(0.4))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.cyan.opacity(0.3), lineWidth: 1)
        )
    }
}

enum SectionAnchor: String {
    case liveSignals
    case bitcoinDominance
    case topSignals
    case historicalSignals
    case watchlist
    case marketBreadth
    case assetsTraded
    case codeExplanation
    case upgrade
}

struct QuickNavigation: View {
    let onSelect: (SectionAnchor) -> Void

    private let items: [(SectionAnchor, String)] = [
        (.liveSignals, "Live Signals"),
        (.bitcoinDominance, "BTC Dominance"),
        (.topSignals, "Top Signals"),
        (.historicalSignals, "Historical"),
        (.watchlist, "Watchlist"),
        (.marketBreadth, "Market Breadth"),
        (.assetsTraded, "Assets Traded"),
        (.codeExplanation, "Code Explanation"),
        (.upgrade, "Upgrade")
    ]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(items, id: \.0) { item in
                    Button(action: { onSelect(item.0) }) {
                        Text(item.1)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                Capsule().fill(Color.white.opacity(0.12))
                            )
                            .overlay(
                                Capsule().stroke(Color.cyan.opacity(0.3), lineWidth: 1)
                            )
                    }
                }
            }
            .padding(.vertical, 4)
        }
    }
}

struct LiveSignalsSection: View {
    let cryptoSignals: [Signal]
    let stockSignals: [Signal]
    let selectedFilter: Filter

    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Live Signals", subtitle: "Crypto + Stock")
            if selectedFilter == .all || selectedFilter == .crypto {
                SignalList(title: "Crypto Signals", signals: cryptoSignals)
            }
            if selectedFilter == .all || selectedFilter == .stocks {
                SignalList(title: "Stock Signals", signals: stockSignals)
            }
        }
        .padding(14)
        .background(Color.black.opacity(0.35))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.cyan.opacity(0.25), lineWidth: 1)
        )
    }
}

struct SignalList: View {
    let title: String
    let signals: [Signal]

    var body: some View {
        VStack(spacing: 10) {
            HStack {
                Text(title)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
                Text("\(signals.count) signals")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.6))
            }
            if signals.isEmpty {
                EmptyState(text: "Waiting for signals...")
            } else {
                ForEach(signals.prefix(8)) { signal in
                    SignalCard(signal: signal)
                }
            }
        }
    }
}

struct BitcoinDominanceSection: View {
    let value: Double?

    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Bitcoin Dominance", subtitle: "Market share snapshot")
            if let value {
                Text(String(format: "%.2f%%", value))
                    .font(.system(size: 28, weight: .heavy, design: .rounded))
                    .foregroundColor(.yellow)
                Text("From CoinGecko global market data")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.7))
            } else {
                EmptyState(text: "Loading BTC dominance...")
            }
        }
        .padding(14)
        .background(Color.orange.opacity(0.2))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.orange.opacity(0.6), lineWidth: 1)
        )
    }
}

struct TopSignalsSection: View {
    let signals: [Signal]

    var body: some View {
        let buys = signals.filter { $0.direction == "BUY" }
        let sells = signals.filter { $0.direction == "SELL" }

        return VStack(spacing: 12) {
            SectionHeader(title: "Top Signals", subtitle: "Highest confidence")
            SignalList(title: "Top Buys", signals: Array(buys.prefix(4)))
            SignalList(title: "Top Sells", signals: Array(sells.prefix(4)))
        }
        .padding(14)
        .background(Color.blue.opacity(0.2))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.blue.opacity(0.5), lineWidth: 1)
        )
    }
}

struct HistoricalSignalsSection: View {
    let historicalCrypto: [Signal]
    let historicalStock: [Signal]

    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Historical Signals", subtitle: "Crypto 1+ days • Stocks 7+ days")
            VStack(alignment: .leading, spacing: 10) {
                Text("📜 Historical Crypto (1+ days old)")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)
                if historicalCrypto.isEmpty {
                    EmptyState(text: "No archived crypto signals.")
                } else {
                    ForEach(historicalCrypto.prefix(6)) { signal in
                        SignalCard(signal: signal)
                    }
                }
            }
            VStack(alignment: .leading, spacing: 10) {
                Text("📈 Historical Stock & ETF (7+ days old)")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)
                if historicalStock.isEmpty {
                    EmptyState(text: "No archived stock signals.")
                } else {
                    ForEach(historicalStock.prefix(6)) { signal in
                        SignalCard(signal: signal)
                    }
                }
            }
        }
        .padding(14)
        .background(Color.black.opacity(0.35))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.cyan.opacity(0.25), lineWidth: 1)
        )
    }
}

struct CodeExplanationEntry: View {
    @Binding var showCodeExplanation: Bool

    var body: some View {
        Button(action: { showCodeExplanation = true }) {
            HStack(spacing: 12) {
                Text("🔧")
                    .font(.system(size: 24))
                VStack(alignment: .leading, spacing: 4) {
                    Text("Code Explanation")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(.white)
                    Text("Indicators, filters & how signals work")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.white.opacity(0.7))
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(Color.white.opacity(0.7))
            }
            .padding(14)
            .background(Color.purple.opacity(0.25))
            .cornerRadius(18)
            .overlay(
                RoundedRectangle(cornerRadius: 18)
                    .stroke(Color.purple.opacity(0.6), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

struct CodeExplanationPage: View {
    let onDismiss: () -> Void

    var body: some View {
        ZStack {
            SynthwaveBackground()
            VStack(spacing: 0) {
                HStack {
                    Text("🔧 Code Explanation")
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.white)
                    Spacer()
                    Button(action: onDismiss) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 28))
                            .foregroundColor(.white.opacity(0.8))
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color.black.opacity(0.4))

                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        explanationBlock(
                            title: "Signal timing & repainting",
                            body: "Signals are delayed intentionally so the bot can look back in time and confirm the signal was real using historical data that can no longer be changed. Preliminary signals fire on the backend but only appear here once enough time has passed and signal confluence is met."
                        )
                        explanationBlock(
                            title: "Bitcoin Dominance filter",
                            body: "2-period EMA of Bitcoin's market cap percentage. Buy signals are blocked when dominance is above the 2 EMA (rising, bearish for altcoins) and allowed when below (falling, bullish for altcoins). Uses historical CSV and daily API updates."
                        )
                        explanationBlock(
                            title: "Regime filter (BTC halving)",
                            body: "Weekly EMA(20), price vs EMA + 0.25 ATR, optional RSI momentum (70 threshold), and bullish/bearish/caution counters."
                        )
                        explanationBlock(
                            title: "Indicators & divergence",
                            body: "Indicator suite and divergence logic align with the comprehensive analysis on the web. Understanding divergences helps interpret when price and momentum disagree."
                        )
                    }
                    .padding(20)
                }
            }
        }
    }

    private func explanationBlock(title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 15, weight: .bold))
                .foregroundColor(.cyan)
            Text(body)
                .font(.system(size: 14, weight: .regular))
                .foregroundColor(Color.white.opacity(0.9))
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(Color.black.opacity(0.35))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.cyan.opacity(0.3), lineWidth: 1)
        )
    }
}

struct WatchlistSection: View {
    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Watchlist", subtitle: "Your saved assets")
            EmptyState(text: "Add symbols to your watchlist.")
        }
        .padding(14)
        .background(Color.yellow.opacity(0.15))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.yellow.opacity(0.5), lineWidth: 1)
        )
    }
}

struct MarketBreadthSection: View {
    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Market Breadth", subtitle: "Breadth + sentiment")
            EmptyState(text: "Market breadth data will appear here.")
        }
        .padding(14)
        .background(Color.purple.opacity(0.18))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.purple.opacity(0.5), lineWidth: 1)
        )
    }
}

struct AssetsTradedSection: View {
    var body: some View {
        VStack(spacing: 12) {
            SectionHeader(title: "Assets Traded", subtitle: "Crypto + Stocks")
            EmptyState(text: "Assets traded list will load here.")
        }
        .padding(14)
        .background(Color.green.opacity(0.12))
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.green.opacity(0.4), lineWidth: 1)
        )
    }
}

struct SectionHeader: View {
    let title: String
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(.white)
            Text(subtitle)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.white.opacity(0.7))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct EmptyState: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(Color.white.opacity(0.7))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(Color.white.opacity(0.08))
            .cornerRadius(12)
    }
}

struct SignalCard: View {
    let signal: Signal

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(signal.tint.opacity(0.2))
                    .frame(width: 46, height: 46)
                Text(signal.icon)
                    .font(.system(size: 22))
            }
            VStack(alignment: .leading, spacing: 6) {
                Text(signal.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)
                Text(signal.subtitle)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.7))
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 6) {
                Text(signal.direction)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(signal.directionColor)
                Text(signal.confidence)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color.white.opacity(0.7))
            }
        }
        .padding(12)
        .background(Color.white.opacity(0.07))
        .cornerRadius(14)
    }
}

struct UpgradeCTA: View {
    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Text("Unlock Pro Signals")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white)
                Text("In-App Purchase via Apple • Manage in App Store")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.7))
            }
            Spacer()
            Button(action: {}) {
                Text("Upgrade")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.black)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(Color.yellow)
                    .cornerRadius(10)
            }
        }
        .padding(14)
        .background(Color.black.opacity(0.4))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.yellow.opacity(0.5), lineWidth: 1)
        )
    }
}

struct SynthwaveBackground: View {
    var body: some View {
        LinearGradient(
            colors: [
                Color(red: 0.04, green: 0.05, blue: 0.15),
                Color(red: 0.10, green: 0.05, blue: 0.20),
                Color(red: 0.08, green: 0.13, blue: 0.24),
                Color(red: 0.06, green: 0.20, blue: 0.38),
                Color(red: 0.04, green: 0.05, blue: 0.15)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
        .overlay(
            GridOverlay()
                .opacity(0.15)
        )
        .overlay(
            LinearGradient(
                colors: [Color.pink.opacity(0.25), .clear],
                startPoint: .bottom,
                endPoint: .top
            )
        )
    }
}

struct GridOverlay: View {
    var body: some View {
        GeometryReader { geo in
            Path { path in
                let spacing: CGFloat = 36
                let width = geo.size.width
                let height = geo.size.height

                var x: CGFloat = 0
                while x <= width {
                    path.move(to: CGPoint(x: x, y: 0))
                    path.addLine(to: CGPoint(x: x, y: height))
                    x += spacing
                }

                var y: CGFloat = 0
                while y <= height {
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: width, y: y))
                    y += spacing
                }
            }
            .stroke(Color.cyan.opacity(0.25), lineWidth: 0.6)
        }
    }
}

struct NeonToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: 8) {
            configuration.label
            RoundedRectangle(cornerRadius: 12)
                .fill(configuration.isOn ? Color.cyan : Color.white.opacity(0.15))
                .frame(width: 40, height: 22)
                .overlay(
                    Circle()
                        .fill(configuration.isOn ? Color.black : Color.white)
                        .frame(width: 18, height: 18)
                        .offset(x: configuration.isOn ? 9 : -9)
                        .animation(.easeInOut(duration: 0.2), value: configuration.isOn)
                )
                .onTapGesture { configuration.isOn.toggle() }
        }
    }
}

enum Filter: CaseIterable {
    case all
    case crypto
    case stocks

    var title: String {
        switch self {
        case .all: return "All"
        case .crypto: return "Crypto"
        case .stocks: return "Stocks"
        }
    }
}

enum SignalCategory {
    case crypto
    case stocks
}

struct Signal: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let subtitle: String
    let direction: String
    let confidence: String
    let category: SignalCategory
    let tint: Color

    var directionColor: Color {
        direction == "BUY" ? Color.green : Color.pink
    }

    static let sample: [Signal] = [
        Signal(icon: "₿", title: "BTC/USD", subtitle: "Breakout above 63,200", direction: "BUY", confidence: "96% ML Confidence", category: .crypto, tint: .yellow),
        Signal(icon: "◎", title: "ETH/USD", subtitle: "Momentum reversal", direction: "BUY", confidence: "91% ML Confidence", category: .crypto, tint: .cyan),
        Signal(icon: "📈", title: "AAPL", subtitle: "Earnings run-up", direction: "BUY", confidence: "88% ML Confidence", category: .stocks, tint: .orange),
        Signal(icon: "📉", title: "TSLA", subtitle: "Volatility fade", direction: "SELL", confidence: "82% ML Confidence", category: .stocks, tint: .pink)
    ]
}

@MainActor
final class SignalsViewModel: ObservableObject {
    @Published var signals: [Signal] = []
    @Published var statusText: String = "Connecting..."
    @Published var isConnected: Bool = false
    @Published var bitcoinDominance: Double? = nil

    /// Crypto signals older than 1 day (matches signals.html historical).
    var historicalCryptoSignals: [Signal] {
        let cutoff = Calendar.current.date(byAdding: .day, value: -1, to: Date()) ?? Date()
        return signals.filter { $0.category == .crypto && (($0.timestamp ?? .distantFuture) < cutoff) }
    }

    /// Stock signals older than 7 days (matches signals.html historical).
    var historicalStockSignals: [Signal] {
        let cutoff = Calendar.current.date(byAdding: .day, value: -7, to: Date()) ?? Date()
        return signals.filter { $0.category == .stocks && (($0.timestamp ?? .distantFuture) < cutoff) }
    }

    private let service = SignalsService()
    private var timer: Timer?

    func start() async {
        if timer == nil {
            await refresh()
            timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
                Task { await self?.refresh() }
            }
        }
    }

    func refresh() async {
        statusText = "Fetching signals..."
        do {
            async let fetchedSignals = service.fetchSignals()
            async let fetchedDominance = service.fetchBitcoinDominance()
            signals = try await fetchedSignals
            bitcoinDominance = try? await fetchedDominance
            isConnected = true
            statusText = "Live • Updated \(DateFormatter.signalTime.string(from: Date())) UTC"
        } catch {
            isConnected = false
            statusText = "Offline • \(error.localizedDescription)"
        }
    }
}

struct SignalsService {
    private let baseURL = URL(string: "https://brianstreckfus.com/")!
    private let decoder = JSONDecoder()

    func fetchSignals() async throws -> [Signal] {
        let signalsURL = baseURL.appendingPathComponent("signals/signals.json")
        if let signals = try await loadSignalsArray(from: signalsURL) {
            return signals
        }

        let latestURL = baseURL.appendingPathComponent("signals/latest.json")
        if let latest = try await loadSignalsArray(from: latestURL) {
            return latest
        }

        throw URLError(.badServerResponse)
    }

    private func loadSignalsArray(from url: URL) async throws -> [Signal]? {
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse, (200..<300).contains(httpResponse.statusCode) else {
            return nil
        }

        if let rawArray = try? decoder.decode([RawSignal].self, from: data) {
            return rawArray.map { Signal.from(raw: $0) }
        }

        if let rawSingle = try? decoder.decode(RawSignal.self, from: data) {
            return [Signal.from(raw: rawSingle)]
        }

        return nil
    }

    func fetchBitcoinDominance() async throws -> Double {
        let url = URL(string: "https://api.coingecko.com/api/v3/global")!
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse, (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }
        let payload = try decoder.decode(GlobalMarketResponse.self, from: data)
        guard let btcDominance = payload.data.marketCapPercentage["btc"] else {
            throw URLError(.cannotParseResponse)
        }
        return btcDominance
    }
}

struct RawSignal: Decodable {
    let symbol: String?
    let action: String?
    let side: String?
    let direction: String?
    let note: String?
    let source: String?
    let confidence: Double?
    let assetType: String?
    let price: Double?
    let timestamp: String?
    let receivedAt: String?

    enum CodingKeys: String, CodingKey {
        case symbol
        case action
        case side
        case direction
        case note
        case source
        case confidence
        case assetType = "asset_type"
        case price
        case timestamp
        case receivedAt = "received_at"
    }

    /// Parse ISO8601 or common timestamp string to Date for recent vs historical split.
    static func parseDate(_ value: String?) -> Date? {
        guard let value = value, !value.isEmpty else { return nil }
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = iso.date(from: value) { return date }
        iso.formatOptions = [.withInternetDateTime]
        if let date = iso.date(from: value) { return date }
        let fallback = DateFormatter()
        fallback.dateFormat = "yyyy-MM-dd HH:mm:ss"
        fallback.timeZone = TimeZone(secondsFromGMT: 0)
        return fallback.date(from: value)
    }
}

struct GlobalMarketResponse: Decodable {
    let data: GlobalMarketData
}

struct GlobalMarketData: Decodable {
    let marketCapPercentage: [String: Double]

    enum CodingKeys: String, CodingKey {
        case marketCapPercentage = "market_cap_percentage"
    }
}

extension Signal {
    static func from(raw: RawSignal) -> Signal {
        let symbol = (raw.symbol ?? "UNKNOWN").uppercased()
        let directionValue = (raw.action ?? raw.side ?? raw.direction ?? "NEUTRAL").uppercased()
        let category = SignalCategory.from(assetType: raw.assetType, symbol: symbol)
        let icon = SignalIcon.icon(for: symbol, category: category)
        let subtitle = SignalSubtitle.build(note: raw.note, price: raw.price, source: raw.source)
        let confidence = SignalConfidence.build(value: raw.confidence)

        return Signal(
            icon: icon,
            title: symbol,
            subtitle: subtitle,
            direction: directionValue,
            confidence: confidence,
            category: category,
            tint: category.tint
        )
    }
}

enum SignalIcon {
    static func icon(for symbol: String, category: SignalCategory) -> String {
        if symbol.contains("ETH") { return "◎" }
        switch category {
        case .crypto: return "₿"
        case .stocks: return "📈"
        }
    }
}

enum SignalSubtitle {
    static func build(note: String?, price: Double?, source: String?) -> String {
        if let note, !note.isEmpty { return note }
        if let price { return "Price: \(String(format: "%.2f", price))" }
        if let source, !source.isEmpty { return "Source: \(source)" }
        return "Live ML signal"
    }
}

enum SignalConfidence {
    static func build(value: Double?) -> String {
        guard let value else { return "ML Confidence" }
        let percent = Int((value * 100).rounded())
        if percent > 0 && percent <= 100 {
            return "\(percent)% ML Confidence"
        }
        return "ML Confidence"
    }
}

extension SignalCategory {
    static func from(assetType: String?, symbol: String) -> SignalCategory {
        let type = assetType?.lowercased() ?? ""
        if type.contains("stock") { return .stocks }
        return .crypto
    }

    var tint: Color {
        switch self {
        case .crypto: return .yellow
        case .stocks: return .orange
        }
    }
}

extension DateFormatter {
    static let signalTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        return formatter
    }()
}

#Preview {
    SignalsAppView()
}
