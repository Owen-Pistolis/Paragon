using System.ComponentModel.DataAnnotations.Schema;

namespace ParagonWebAPI.Types
{
    public class Organization
    {
        public string ID { get; set; }
        public string Name { get; set; }
        public User? OrganizationManager { get; set; }
        public string? OrganizationManagerID { get; set; }
        [NotMapped]
        public List<User> Users { get; set; }
        //[NotMapped]
        //public List<Data> OrganizationData { get; set; }

        public Organization() { 
            
        }
    }
}
