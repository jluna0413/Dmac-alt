#!/usr/bin/env python3
"""
Test script to verify Byterover RAG functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

def test_rag_tools():
    """Test RAG search functionality"""
    print("=== Testing Byterover RAG functionality ===")

    try:
        # Test basic availability
        print("✓ Testing RAG module import...")
        from services.rag_search_module import RAGSearch

        # Initialize RAG
        rag = RAGSearch()
        print("✓ RAG module initialized")

        # Test basic query
        print("✓ Testing basic search...")
        results = rag.search("web crawling", top_k=3)
        print(f"Found {len(results)} results for 'web crawling'")

        if results:
            print("Top results:")
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result.get('title', 'No title')}")
                print(f"     {result.get('url', 'No URL')}")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_web_crawling():
    """Test web crawling functionality"""
    print("\n=== Testing Web Crawling ===")

    try:
        print("✓ Testing crawler import...")
        from services.web_crawler import WebCrawler

        # Initialize crawler
        crawler = WebCrawler()
        print("✓ Web crawler initialized")

        # Test with a simple URL
        test_url = "https://httpbin.org/html"
        print(f"✓ Testing crawl of {test_url}...")

        content = crawler.crawl(test_url, max_depth=1)
        print(f"✓ Crawl successful, content length: {len(content) if content else 0}")

        if content and len(content) > 100:
            print("Sample content (first 200 chars):")
            print(content[:200] + "..." if len(content) > 200 else content)

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Crawl failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Byterover RAG tests...")

    rag_success = test_rag_tools()
    crawl_success = test_web_crawling()

    print("\n=== Test Results ===")
    print("RAG Tests: ✓" if rag_success else "RAG Tests: ✗")
    print("Crawl Tests: ✓" if crawl_success else "Crawl Tests: ✗")
    print("Overall: ✓" if (rag_success and crawl_success) else "Overall: ✗")

    sys.exit(0 if (rag_success and crawl_success) else 1)
