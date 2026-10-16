"""Domain-Driven Design (DDD) Prompt Engine and Few-Shot Golden Bucket Exemplars.

Operationalizes ONT-001 (Retail Business Ontology) and ADR-0007 (Semantic Layer)
to bridge the semantic gap between executive intent and BigQuery GoogleSQL.
"""

import re

from src.bq.schema import DEFAULT_DATASET, SchemaInspector

# Domain Ontology Definitions (ONT-001)
RETAIL_ONTOLOGY_RULES = """
### Domain-Driven Design (DDD) Retail Business Rules (ONT-001):
1. **Net Revenue Calculation Rule:**
   - "Revenue", "Sales", or "Total Earned" MUST ALWAYS strictly exclude Cancelled and Returned orders.
   - Formula: `SUM(order_items.sale_price) WHERE status NOT IN ('Cancelled', 'Returned')`.
   - Never compute Net Revenue by summing raw GMV without this status filter.

2. **Gross Profit Margin Calculation Rule:**
   - "Margin", "Gross Profit", or "Profitability" requires joining `order_items` with `products` on `order_items.product_id = products.id`.
   - Profit Formula: `SUM(order_items.sale_price - products.cost)`.
   - Margin Percentage Formula: `SAFE_DIVIDE(SUM(order_items.sale_price - products.cost), SUM(order_items.sale_price)) * 100`.
   - Exclude Cancelled and Returned items unless specifically analyzing return losses.

3. **Customer Churn Calculation Rule:**
   - The dataset has NO `churn` column. Churn is a temporal cohort behavior.
   - Definition: A registered customer who placed at least one order historically but has zero orders in the trailing 90 days.
   - Formula: Use a CTE to find `MAX(orders.created_at)` per user, then count users where `MAX(created_at) < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)` on orders where `status NOT IN ('Cancelled')`.

4. **Average Order Value (AOV):**
   - Formula: `SAFE_DIVIDE(SUM(sale_price), COUNT(DISTINCT order_id)) WHERE status NOT IN ('Cancelled', 'Returned')`.

5. **Return Rate Percentage:**
   - Formula: `SAFE_DIVIDE(COUNTIF(status = 'Returned'), COUNTIF(status IN ('Complete', 'Shipped', 'Returned'))) * 100`.
"""

# Golden Bucket Trios (Exemplars for in-context few-shot learning)
GOLDEN_BUCKET_EXEMPLARS = f"""
### Few-Shot Golden Exemplars:

---
**Exemplar 1: Category Net Revenue**
*Executive Question:* "What is our Net Revenue by product category for the last 6 months?"
*GoogleSQL:*
```sql
SELECT
    p.category,
    ROUND(SUM(oi.sale_price), 2) AS net_revenue_usd,
    COUNT(DISTINCT oi.order_id) AS total_orders
FROM `{DEFAULT_DATASET}.order_items` oi
JOIN `{DEFAULT_DATASET}.products` p ON oi.product_id = p.id
WHERE oi.status NOT IN ('Cancelled', 'Returned')
  AND oi.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 180 DAY)
GROUP BY p.category
ORDER BY net_revenue_usd DESC;
```

---
**Exemplar 2: Brand Profitability Margins**
*Executive Question:* "Which brands produce our highest gross profit margins?"
*GoogleSQL:*
```sql
SELECT
    p.brand,
    ROUND(SUM(oi.sale_price), 2) AS total_revenue,
    ROUND(SUM(p.cost), 2) AS total_cogs,
    ROUND(SUM(oi.sale_price - p.cost), 2) AS gross_profit,
    ROUND(SAFE_DIVIDE(SUM(oi.sale_price - p.cost), SUM(oi.sale_price)) * 100, 2) AS gross_margin_pct
FROM `{DEFAULT_DATASET}.order_items` oi
JOIN `{DEFAULT_DATASET}.products` p ON oi.product_id = p.id
WHERE oi.status NOT IN ('Cancelled', 'Returned')
GROUP BY p.brand
ORDER BY gross_profit DESC
LIMIT 10;
```

---
**Exemplar 3: Churn Rate Analysis**
*Executive Question:* "How many customers are currently churned across our customer base?"
*GoogleSQL:*
```sql
WITH customer_orders AS (
    SELECT
        user_id,
        MAX(created_at) AS last_order_date
    FROM `{DEFAULT_DATASET}.orders`
    WHERE status NOT IN ('Cancelled')
    GROUP BY user_id
)
SELECT
    COUNTIF(last_order_date < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)) AS churned_customers,
    COUNT(user_id) AS total_active_customers,
    ROUND(SAFE_DIVIDE(COUNTIF(last_order_date < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)), COUNT(user_id)) * 100, 2) AS churn_rate_pct
FROM customer_orders;
```
"""


def strip_markdown_fences(sql: str) -> str:
    """Robustly strip markdown code fences, comments, and trailing semicolons from SQL output."""
    if not sql:
        return ""

    clean = sql.strip()
    # Strip leading markdown code blocks (```sql, ```SQL, ```)
    clean = re.sub(r"^```(?:sql|SQL)?\s*", "", clean)
    # Strip trailing markdown code blocks (```)
    clean = re.sub(r"\s*```$", "", clean)
    clean = clean.strip()
    # Strip trailing semicolon for consistency
    return clean.rstrip(";").strip()


def build_system_prompt(
    schema_inspector: SchemaInspector | None = None,
    dataset_id: str = DEFAULT_DATASET,
    allowed_brands: list[str] | None = None,
) -> str:
    """Construct the comprehensive system instruction prompt for GoogleSQL generation."""
    inspector = schema_inspector or SchemaInspector(client=None, dataset_id=dataset_id)
    schema_text = inspector.format_schema_for_prompt()

    brand_scoping_instruction = ""
    if allowed_brands:
        brands_list = ", ".join(f"'{b}'" for b in allowed_brands)
        brand_scoping_instruction = f"""
### Enterprise Brand Scoping Guardrail (MANDATORY):
- The current user has access RESTRICTED strictly to the following brand(s): [{brands_list}].
- Whenever querying tables related to merchandise (`products`, or `order_items` joined with `products`), you MUST inject a filter on brand:
  `WHERE p.brand IN ({brands_list})` or `WHERE brand IN ({brands_list})`.
- EXCEPTION: If the user query ONLY inspects customer demographic data on `users` (e.g. state counts, ages) where no brand column exists, DO NOT hallucinate a brand column on `users`.
"""

    return f"""You are the Lead Retail Data Engineering AI Assistant for TheLook eCommerce.
Your role is to translate executive natural language questions into high-performance, standard GoogleSQL queries.

{schema_text}

{RETAIL_ONTOLOGY_RULES}

{brand_scoping_instruction}

### SQL Technical Standards:
1. Always construct queries conforming to GoogleSQL syntax for BigQuery.
2. Tables MUST be fully qualified using `{dataset_id}.<table_name>`.
3. Use `SAFE_DIVIDE(numerator, denominator)` for all division operations to prevent division-by-zero errors.
4. For temporal filtering, use BigQuery functions such as `TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL X DAY)`.
5. Output ONLY the raw SQL query. Do NOT include markdown code fences (no ```sql or ```), explanations, preambles, or conversational commentary.

{GOLDEN_BUCKET_EXEMPLARS}
"""


def build_user_prompt(
    user_query: str,
    error_feedback: str | None = None,
    previous_sql: str | None = None,
) -> str:
    """Construct the user prompt with query context and optional self-correction feedback."""
    prompt_parts = [f"Executive Request: {user_query}"]

    if error_feedback and previous_sql:
        prompt_parts.append("\n---")
        prompt_parts.append("### Diagnostic Self-Correction Feedback:")
        prompt_parts.append(
            f"Your previous query failed or returned anomalous results:\n```sql\n{previous_sql}\n```"
        )
        prompt_parts.append(f"Diagnostic Feedback: {error_feedback}")
        prompt_parts.append(
            "Carefully analyze the schema and error above. Correct the SQL and output the revised GoogleSQL query."
        )

    return "\n".join(prompt_parts)
