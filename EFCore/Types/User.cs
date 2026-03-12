using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ParagonWebAPI.Types
{
    public class User
    {
        public string ID { get; set; }
        [StringLength(30)]
        public string Email { get; set; }
        [StringLength(30)]
        public string FirstName { get; set; }
        [StringLength(30)]
        public string LastName { get; set; }
        public Organization? Organization { get; set; }
        public string? OrganizationID { get; set; }
        public User() {
        
        }
    }
}
