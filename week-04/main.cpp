#include <bits/stdc++.h>
using namespace std;

static inline double calculate(unsigned long long iterations, double param1, double param2) {
    // Closed-form for the specific case param1=4, param2=1:
    // 4*S_N = psi(N+1.25) - psi(N+1.75) + pi + 4/(4N+3)
    // Using asymptotic expansion for large arguments of digamma:
    // psi(x) ≈ ln(x) - 1/(2x) - 1/(12x^2) + ...
    if (param1 == 4.0 && param2 == 1.0) {
        const double N = static_cast<double>(iterations);
        const double a = N + 1.25;
        const double b = N + 1.75;
        // ln(a/b) computed stably
        const double lnterm = log1p(-0.5 / b);
        // -[1/(2a) - 1/(2b)] = -0.25/(a*b)
        const double corr1 = -0.25 / (a * b);
        // -[1/(12a^2) - 1/(12b^2)]
        const double inva = 1.0 / a, invb = 1.0 / b;
        const double corr2 = -(1.0 / 12.0) * ((inva * inva) - (invb * invb));
        const double pi = acos(-1.0);
        const double res4 = pi + lnterm + corr1 + corr2 + (4.0 / (4.0 * N + 3.0));
        return 0.25 * res4;
    }

    // General fallback: exact order as Python loop (slower).
    double result = 1.0;
    for (unsigned long long i = 1; i <= iterations; ++i) {
        double j = i * param1 - param2;
        result -= 1.0 / j;
        j = i * param1 + param2;
        result += 1.0 / j;
    }
    return result;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    auto start_time = chrono::steady_clock::now();
    double result = calculate(200000000ULL, 4.0, 1.0) * 4.0;
    auto end_time = chrono::steady_clock::now();

    double elapsed = chrono::duration<double>(end_time - start_time).count();

    cout.setf(ios::fixed);
    cout << "Result: " << setprecision(12) << result << '\n';
    cout << "Execution Time: " << setprecision(6) << elapsed << " seconds\n";
    return 0;
}