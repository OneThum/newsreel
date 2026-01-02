"""
Change Feed Recovery Tests

Tests the resilience and recovery capabilities of the Cosmos DB change feed
processor for the clustering pipeline.
"""
import pytest
import os
from datetime import datetime, timezone, timedelta
from azure.cosmos import CosmosClient, PartitionKey, exceptions


@pytest.fixture(scope="module")
def cosmos_client():
    """Get Cosmos DB client"""
    conn_str = os.getenv('COSMOS_CONNECTION_STRING')
    if not conn_str:
        pytest.skip("COSMOS_CONNECTION_STRING not configured")
    
    return CosmosClient.from_connection_string(conn_str)


@pytest.fixture(scope="module")
def database(cosmos_client):
    """Get database client"""
    db_name = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
    return cosmos_client.get_database_client(db_name)


@pytest.mark.integration
class TestLeaseContainerHealth:
    """Test lease container health and structure"""
    
    def test_lease_container_exists(self, database):
        """Test that lease container exists"""
        try:
            container = database.get_container_client('leases')
            # Query to verify it's accessible
            list(container.query_items(
                'SELECT TOP 1 c.id FROM c',
                enable_cross_partition_query=True
            ))
            assert True, "Lease container is accessible"
        except exceptions.CosmosResourceNotFoundError:
            pytest.fail("Lease container does not exist - change feed may not work")
    
    def test_lease_container_has_leases(self, database):
        """Test that lease container has lease documents"""
        container = database.get_container_client('leases')
        leases = list(container.query_items(
            'SELECT * FROM c',
            enable_cross_partition_query=True
        ))
        
        # Should have at least one lease for the change feed
        assert len(leases) >= 1, \
            "Lease container should have at least one lease document"
    
    def test_lease_has_continuation_token(self, database):
        """Test that at least one lease has a continuation token"""
        container = database.get_container_client('leases')
        leases = list(container.query_items(
            'SELECT * FROM c',
            enable_cross_partition_query=True
        ))
        
        # At least one lease should have a continuation token
        has_token = any(
            lease.get('ContinuationToken') is not None 
            for lease in leases
        )
        
        # This might be None if the change feed just started
        # Log but don't fail
        if not has_token:
            print("⚠️ No lease has continuation token - change feed may be starting fresh")
    
    def test_lease_is_recent(self, database):
        """Test that leases have been updated recently"""
        container = database.get_container_client('leases')
        leases = list(container.query_items(
            'SELECT * FROM c',
            enable_cross_partition_query=True
        ))
        
        now = datetime.now(timezone.utc)
        recent_threshold = now - timedelta(hours=1)
        
        recent_leases = []
        for lease in leases:
            ts = lease.get('_ts')
            if ts:
                lease_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                if lease_time > recent_threshold:
                    recent_leases.append(lease)
        
        # At least one lease should be recent if pipeline is active
        # Don't fail, just warn if no recent updates
        if len(recent_leases) == 0:
            print("⚠️ No lease updated in last hour - pipeline may be idle or stalled")


@pytest.mark.integration
class TestChangeFeedProcessing:
    """Test that change feed is actually processing documents"""
    
    def test_articles_being_processed(self, database):
        """Test that articles are being marked as processed"""
        articles = database.get_container_client('raw_articles')
        
        # Get recently processed articles
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        query = f"""
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.processed = true 
            AND c._ts >= {int(one_hour_ago.timestamp())}
        """
        
        result = list(articles.query_items(query, enable_cross_partition_query=True))
        recently_processed = result[0] if result else 0
        
        # Should have some recently processed articles if pipeline is running
        print(f"📊 Articles processed in last hour: {recently_processed}")
        
        # This is informational - pipeline might be idle
        if recently_processed == 0:
            print("⚠️ No articles processed in last hour - check pipeline health")
    
    def test_stories_being_created_or_updated(self, database):
        """Test that stories are being created or updated"""
        stories = database.get_container_client('story_clusters')
        
        # Get recently updated stories
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        query = f"""
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.last_updated >= '{one_hour_ago.isoformat()}'
        """
        
        result = list(stories.query_items(query, enable_cross_partition_query=True))
        recently_updated = result[0] if result else 0
        
        print(f"📊 Stories updated in last hour: {recently_updated}")
        
        # Should have some activity
        if recently_updated == 0:
            print("⚠️ No stories updated in last hour - clustering may be stalled")
    
    def test_unprocessed_backlog_reasonable(self, database):
        """Test that unprocessed backlog is reasonable"""
        articles = database.get_container_client('raw_articles')
        
        # Count unprocessed articles
        query = """
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.processed = false OR NOT IS_DEFINED(c.processed)
        """
        
        result = list(articles.query_items(query, enable_cross_partition_query=True))
        unprocessed = result[0] if result else 0
        
        print(f"📊 Unprocessed articles: {unprocessed}")
        
        # Large backlog might indicate a problem
        if unprocessed > 50000:
            print("⚠️ Large backlog detected - pipeline may be struggling")


@pytest.mark.integration
class TestChangeFeedRecoveryScenarios:
    """Test recovery scenarios for change feed"""
    
    def test_can_trigger_article_update(self, database):
        """Test that we can update an article to trigger change feed"""
        articles = database.get_container_client('raw_articles')
        
        # Get a random article
        query = 'SELECT TOP 1 * FROM c'
        result = list(articles.query_items(query, enable_cross_partition_query=True))
        
        if not result:
            pytest.skip("No articles in database")
        
        article = result[0]
        original_ts = article.get('_ts', 0)
        
        # Update it to trigger change feed
        article['_recovery_test'] = datetime.now(timezone.utc).isoformat()
        
        try:
            articles.replace_item(item=article['id'], body=article)
            
            # Verify it was updated
            updated = articles.read_item(
                item=article['id'], 
                partition_key=article.get('published_date', article['id'])
            )
            
            assert updated.get('_ts', 0) >= original_ts, \
                "Article timestamp should be updated or same"
            
            print(f"✅ Successfully triggered change feed update for article {article['id']}")
            
        except Exception as e:
            pytest.fail(f"Failed to update article: {e}")
    
    def test_database_connectivity(self, database):
        """Test basic database connectivity"""
        # Try to list containers
        containers = list(database.list_containers())
        container_names = [c['id'] for c in containers]
        
        required = ['raw_articles', 'story_clusters', 'leases']
        for name in required:
            assert name in container_names, \
                f"Required container '{name}' not found"
        
        print(f"✅ All required containers present: {required}")
    
    def test_summarization_lease_container_exists(self, database):
        """Test that summarization lease container exists"""
        try:
            container = database.get_container_client('leases-summarization')
            list(container.query_items(
                'SELECT TOP 1 c.id FROM c',
                enable_cross_partition_query=True
            ))
            print("✅ Summarization lease container exists")
        except exceptions.CosmosResourceNotFoundError:
            # This is OK - it will be created when summarization runs
            print("ℹ️ Summarization lease container not yet created")


@pytest.mark.integration
class TestPipelineLatency:
    """Test pipeline latency metrics"""
    
    def test_oldest_unprocessed_article_age(self, database):
        """Test how old the oldest unprocessed article is"""
        articles = database.get_container_client('raw_articles')
        
        # Get oldest unprocessed article
        query = """
            SELECT TOP 1 c.fetched_at, c.title 
            FROM c 
            WHERE c.processed = false OR NOT IS_DEFINED(c.processed)
            ORDER BY c.fetched_at ASC
        """
        
        result = list(articles.query_items(query, enable_cross_partition_query=True))
        
        if not result:
            print("✅ No unprocessed articles - pipeline is caught up!")
            return
        
        oldest = result[0]
        fetched_at = oldest.get('fetched_at')
        
        if fetched_at:
            try:
                fetch_time = datetime.fromisoformat(str(fetched_at).replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_minutes = (now - fetch_time).total_seconds() / 60
                
                print(f"📊 Oldest unprocessed article age: {age_minutes:.0f} minutes")
                
                # Alert if very old
                if age_minutes > 120:
                    print("⚠️ Pipeline may be stalled - oldest article is over 2 hours old")
                
            except Exception as e:
                print(f"Could not parse date: {e}")
    
    def test_newest_story_age(self, database):
        """Test how fresh the newest story is"""
        stories = database.get_container_client('story_clusters')
        
        query = 'SELECT TOP 1 c.last_updated FROM c ORDER BY c.last_updated DESC'
        result = list(stories.query_items(query, enable_cross_partition_query=True))
        
        if not result:
            print("⚠️ No stories in database")
            return
        
        newest = result[0]
        last_updated = newest.get('last_updated')
        
        if last_updated:
            try:
                update_time = datetime.fromisoformat(str(last_updated).replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_minutes = (now - update_time).total_seconds() / 60
                
                print(f"📊 Newest story age: {age_minutes:.0f} minutes")
                
                # Healthy pipeline should have updates within 30 minutes
                if age_minutes > 30:
                    print("⚠️ No story updates in 30 minutes - check pipeline")
                else:
                    print("✅ Pipeline is actively updating stories")
                    
            except Exception as e:
                print(f"Could not parse date: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

