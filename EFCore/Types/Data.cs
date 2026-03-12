using System.ComponentModel.DataAnnotations.Schema;

namespace ParagonWebAPI.Types
{
    public class Data
    {
        public long ID { get; set; }

        [NotMapped]
        public byte[] SessionData { get; set; }
        public Organization Organization { get; set; }
        public long OrganizationID { get; set; }
        public Data()
        {

        }
    }
}
