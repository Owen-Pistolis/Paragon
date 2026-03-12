using Microsoft.EntityFrameworkCore;
using MongoDB.Bson.IO;
using MongoDB.Bson;
using MongoDB.Driver;
using MongoDB.EntityFrameworkCore.Extensions;
using ParagonWebAPI.Types;

namespace ParagonWebAPI
{
    public class MongoContext : DbContext
    {
        public DbSet<JsonChunk> Chunks { get; set; }
        public DbSet<JsonFull> AssembledChunks { get; set; }

        public MongoContext(DbContextOptions options) : base(options) { }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);
            modelBuilder.Entity<JsonChunk>().ToCollection("chunks");
            modelBuilder.Entity<JsonFull>().ToCollection("assembledChunks");

        }
    }
}
