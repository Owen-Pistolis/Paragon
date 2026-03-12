using Microsoft.EntityFrameworkCore;
using ParagonWebAPI.Types;

namespace ParagonWebAPI
{
    public class MySQLContext : DbContext
    {
        //public DbSet<Data> Sessions { get; set; }
        public DbSet<Organization> Organizations { get; set; }
        public DbSet<User> Users { get; set; }
        public MySQLContext(DbContextOptions<MySQLContext> opitons) : base(opitons) { }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            //modelBuilder.Entity<Data>()
            //    .HasKey(data => data.ID);

            modelBuilder.Entity<User>()
                .HasKey(user => user.ID);

            modelBuilder.Entity<Organization>()
                .HasKey(org => org.ID);

            modelBuilder.Entity<User>()
                .HasOne(o => o.Organization)
                .WithMany(u => u.Users)
                .HasForeignKey(o => o.OrganizationID);

            modelBuilder.Entity<Organization>()
                .HasOne(o => o.OrganizationManager)
                .WithMany()
                .HasForeignKey(o => o.OrganizationManagerID)
                .OnDelete(DeleteBehavior.Restrict);

            //modelBuilder.Entity<Data>()
            //    .HasOne(d => d.Organization)
            //    .WithMany(o => o.OrganizationData)
            //    .HasForeignKey(d => d.OrganizationID);



        }
    }
}
