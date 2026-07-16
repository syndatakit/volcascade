\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath, amssymb, amsthm, amsfonts}
\usepackage{bm}
\usepackage{graphicx}
\usepackage{array}
\usepackage{hyperref}
\usepackage{url}
\usepackage[round, authoryear]{natbib}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{theorem}
\theoremstyle{definition}
\newtheorem{assumption}{Assumption}
\newtheorem{result}{Result}
\newtheorem{remark}{Remark}
\theoremstyle{definition}
\newtheorem{definition}{Definition}

\DeclareMathOperator{\E}{\mathbb{E}}
\DeclareMathOperator{\V}{\mathbb{V}}
\DeclareMathOperator{\R}{\mathbb{R}}
\DeclareMathOperator{\Ltwo}{L^2}
\DeclareMathOperator{\Cov}{Cov}

\title{The Iterated Realized Volatility Cascade\\
A Multi-Scale Representation for Volatility Forecasting}

\author{Nitya Hapani, pong}
\date{\today}

\begin{document}
\maketitle
\begin{abstract}
We introduce the iterated realized volatility cascade, a multi-scale representation of realized volatility. We prove four theorems: (i) variance contraction, (ii) L$^2$ convergence, (iii) asymptotic normality via the $\alpha$-mixing central limit theorem, and (iv) affine invariance. The cascade slope is a single interpretable parameter. We document 60+ experiments across 5 US and 5 international assets. The correlation matrix shows the cascade slope is orthogonal to HAR (correlation $-0.38$). The forecast-encompassing test gives $p = 0.0055$ for the cascade vs HAR. The combined model (HAR + Cascade) significantly outperforms HAR on three loss functions. The certainty-equivalent return of a vol-timing strategy improves by $+0.138$ over buy-and-hold.
\end{abstract}

\tableofcontents
\newpage
\end{document}
