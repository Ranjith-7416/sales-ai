# Knowledge Base Documentation

This directory contains the knowledge base data for the Sales AI system. The RAG (Retrieval Augmented Generation) system uses this data to match customer requirements with solutions.

## Overview

The knowledge base consists of:
- **Products**: Software solutions, platforms, and tools
- **Services**: Professional services, support, and implementation offerings

These are indexed in ChromaDB for semantic search and similarity matching.

## Directory Structure

```
knowledge_base/
├── README.md                    # This file
├── products.json               # Product catalog
├── services.json               # Services catalog
└── case_studies.json          # Case studies (optional)
```

## File Formats

### Products Schema

Each product should follow this structure:

```json
{
  "id": "prod-001",                          // Unique product identifier
  "name": "Product Name",                    // Display name
  "category": "Category Name",               // Product category
  "description": "Full product description", // 1-2 sentence overview
  "features": [                              // Key features/capabilities
    "Feature 1",
    "Feature 2",
    "Feature 3"
  ],
  "pricing": "$X,XXX - $X,XXX/month",       // Price range
  "implementation_timeline": "X-Y weeks",    // Typical implementation time
  "integration_complexity": "Low|Medium|High", // Integration difficulty
  "certifications": [                        // Security/compliance certs
    "ISO 27001",
    "SOC 2 Type II"
  ],
  "supported_formats": [],                   // If applicable
  "api_rate_limit": "X req/min",            // API limits
  "uptime_sla": "99.95%",                   // Service availability
  "support_level": "24/7 Premium"           // Support tier
}
```

### Services Schema

Each service should follow this structure:

```json
{
  "id": "svc-001",                          // Unique service identifier
  "name": "Service Name",                   // Display name
  "category": "Service Category",           // Service category
  "description": "Full service description",// 1-2 sentence overview
  "scope_of_work": [                        // What's included
    "Item 1",
    "Item 2"
  ],
  "duration": "X-Y weeks",                  // Typical duration
  "team_composition": [                     // Who's involved
    "Role 1",
    "Role 2"
  ],
  "pricing": "$X,XXX - $X,XXX",            // Price range
  "deliverables": [                         // Outcomes/outputs
    "Deliverable 1",
    "Deliverable 2"
  ],
  "certifications_provided": [],            // Certs offered
  "additional_notes": "Any special notes"   // Extra info
}
```

### Case Studies Schema (Optional)

```json
{
  "id": "case-001",
  "company_name": "Customer Company",
  "industry": "Industry Vertical",
  "challenge": "What problem they had",
  "solution": "How we solved it",
  "results": [
    "Result 1",
    "Result 2"
  ],
  "roi": "X% ROI or $X saved",
  "testimonial": "Customer quote",
  "timeline": "Implementation duration"
}
```

## Adding Products

### 1. Create Product Entry

Add a new object to `products.json`:

```json
{
  "id": "prod-006",
  "name": "Your Product Name",
  "category": "AI/Analytics/Infrastructure/etc",
  "description": "Brief description",
  "features": ["Feature 1", "Feature 2"],
  "pricing": "$X,XXX/month",
  "implementation_timeline": "2-4 weeks",
  // ... other fields
}
```

### 2. Upload to System

Once added to the JSON file, upload via API:

```bash
curl -X POST http://localhost:8000/api/knowledge-base/products/upload \
  -H "Content-Type: application/json" \
  -d @knowledge_base/products.json
```

### 3. Verify Upload

Search for your product:

```bash
curl "http://localhost:8000/api/knowledge-base/products/search?query=your_product_name"
```

## Adding Services

Follow the same process as products:

1. Add to `services.json`
2. Upload via API:
```bash
curl -X POST http://localhost:8000/api/knowledge-base/services/upload \
  -H "Content-Type: application/json" \
  -d @knowledge_base/services.json
```

3. Verify:
```bash
curl "http://localhost:8000/api/knowledge-base/services/search?query=service_name"
```

## Search API Endpoints

### Search Products

```
GET /api/knowledge-base/products/search?query=<search_term>&limit=5
```

Returns products ordered by relevance score (0-1).

**Example:**
```bash
curl "http://localhost:8000/api/knowledge-base/products/search?query=document%20processing&limit=3"

Response:
[
  {
    "id": "prod-001",
    "name": "DocumentAI Pro",
    "relevance_score": 0.92,
    // ... other fields
  },
  {
    "id": "prod-003",
    "name": "DataVault Analytics",
    "relevance_score": 0.67,
    // ... other fields
  }
]
```

### Search Services

```
GET /api/knowledge-base/services/search?query=<search_term>&limit=5
```

### List All Products

```
GET /api/knowledge-base/products?limit=50&offset=0
```

### List All Services

```
GET /api/knowledge-base/services?limit=50&offset=0
```

## Best Practices

### Writing Descriptions

- **Concise**: 1-2 sentences, focus on value
- **Customer-centric**: Explain benefits, not just features
- **Searchable**: Include industry terms and use cases
- **Accurate**: No marketing fluff or exaggerations

❌ Poor: "Best solution on the market"
✅ Good: "Enterprise document processing with 99.8% OCR accuracy and multi-language support"

### Feature Lists

- **Be specific**: Avoid vague terms
- **Quantify**: Include numbers, percentages, scales
- **Actionable**: Focus on what users can do

❌ Poor: ["Advanced", "Powerful", "Best"]
✅ Good: ["OCR with 99.8% accuracy", "Support for 50+ languages", "Real-time API access"]

### Pricing

- Use realistic ranges: "start with" or "from" for lower bounds
- Include currency and time period (/month, /year, one-time)
- If variable, describe factors: "Depends on data volume and users"

### Timeline

- Be realistic based on complexity
- Account for customer's role (data prep, team availability, etc.)
- Include parallel vs sequential phases

### Certifications

Only include certifications the product/service actually has. This is verified during review stage.

## Quality Assurance

### Before Publishing

1. **Validate JSON**
   ```bash
   python -m json.tool knowledge_base/products.json > /dev/null
   ```

2. **Check for duplicates**
   - Each ID should be unique
   - Product names should be distinct

3. **Verify required fields**
   - id, name, category, description are mandatory
   - Other fields depend on applicability

4. **Test search**
   - Upload and search for each entry
   - Verify relevance scoring makes sense

5. **Cross-reference**
   - Ensure features mentioned are realistic
   - Verify pricing aligns with market
   - Check implementation timelines are reasonable

## Updating Knowledge Base

### To Update an Existing Product

1. Modify the JSON file
2. Re-upload:
   ```bash
   curl -X POST http://localhost:8000/api/knowledge-base/products/upload \
     -H "Content-Type: application/json" \
     -d @knowledge_base/products.json
   ```

3. System will:
   - Delete old embeddings for updated products
   - Create new embeddings
   - Make searchable immediately

### To Remove Products

Delete from JSON and re-upload. Products not in file are removed from vector DB.

## Semantic Search Tuning

The system uses semantic similarity (cosine distance on embeddings). 

**Factors affecting search quality:**

1. **Description quality**: Better descriptions = better matches
2. **Feature lists**: Include keywords customers search for
3. **Categorization**: Helps narrow results
4. **Specificity**: Generic products match many queries (can be good or bad)

### Common Search Queries

Train your knowledge base with these in mind:

- **By problem**: "document processing", "authentication", "data analytics"
- **By industry**: "healthcare CRM", "financial compliance", "retail analytics"
- **By technology**: "Python integration", "Kubernetes support", "API-first"
- **By outcome**: "cost optimization", "security audit", "faster deployment"

## Exporting Knowledge Base

```bash
# Export all products
curl http://localhost:8000/api/knowledge-base/products?limit=1000 \
  > exported_products.json

# Export all services
curl http://localhost:8000/api/knowledge-base/services?limit=1000 \
  > exported_services.json
```

## Troubleshooting

### Products not appearing in search

1. Verify JSON is valid
2. Check upload succeeded (HTTP 200)
3. Wait a few seconds for indexing
4. Search for exact product name first
5. Check logs for errors

### Low relevance scores

- Improve description keywords
- Make features more specific
- Ensure category is accurate
- Add case studies for context

### Duplicate products in results

- Check for duplicate IDs in JSON
- Re-upload to refresh embeddings

## Support

For issues with the knowledge base:
1. Check this documentation
2. Review sample products.json and services.json
3. Test upload endpoint with sample data
4. Check backend logs for errors

---

Last Updated: January 2025
