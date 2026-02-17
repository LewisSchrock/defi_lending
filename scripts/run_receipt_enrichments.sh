#!/bin/bash
#
# Receipt Token Enrichment Pipeline
# Run after BSC completes to fix Compound V2 fork debt valuations
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================================================"
echo "RECEIPT TOKEN ENRICHMENT PIPELINE"
echo "========================================================================"
echo ""

# Function to run enrichment
run_enrichment() {
    local chain=$1
    local protocol=$2

    echo "------------------------------------------------------------------------"
    echo "Enriching: $protocol ($chain)"
    echo "------------------------------------------------------------------------"

    python3 "$SCRIPT_DIR/enrich_with_receipt_tokens.py" --chain "$chain"

    if [ $? -eq 0 ]; then
        echo "✓ $protocol enrichment complete"
        echo ""

        # Convert JSONL to parquet
        echo "Converting to parquet..."
        python3 "$SCRIPT_DIR/convert_enriched_to_parquet.py" "$chain"

        if [ $? -eq 0 ]; then
            echo "✓ $protocol parquet conversion complete"
        else
            echo "✗ $protocol parquet conversion failed"
            return 1
        fi
    else
        echo "✗ $protocol enrichment failed"
        return 1
    fi

    echo ""
}

# Check if BSC is complete
if [ ! -f "$PROJECT_ROOT/data/silver/liquidations/bsc/liquidations_v2.parquet" ]; then
    echo "WARNING: BSC enrichment appears incomplete"
    echo "Expected file: data/silver/liquidations/bsc/liquidations_v2.parquet"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run enrichments sequentially
run_enrichment "avalanche" "Benqi" || exit 1
run_enrichment "linea" "Mendi" || exit 1
run_enrichment "scroll" "LayerBank" || exit 1

echo "========================================================================"
echo "✅ ALL ENRICHMENTS COMPLETE"
echo "========================================================================"
echo ""
echo "NOTE: Receipt token amounts are now correct (underlying tokens),"
echo "      but some prices may be missing from on-chain oracles."
echo ""
echo "Next steps:"
echo "  1. Re-price with DefiLlama caches: python scripts/reprice_enriched_liquidations.py"
echo "  2. Rebuild gold panel: python scripts/build_gold_panel_all_csus.py"
echo "  3. Validate debt values match DeFiLlama ranges"
echo "  4. Run Pedroni PVAR analysis"
echo ""
