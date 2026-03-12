using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;

namespace ParagonWebAPI.Types
{
    [PrimaryKey("ID")]
    public class JsonChunk
    {
        public string ID { get; set; }
        public int ChunkNumber { get; set; }
        public int TotalChunks { get; set; }
        public string Data { get; set; }
        public DateTime Timestamp { get; set; }

        public JsonChunk(int chunkNumber, int totalChunks, string data) {
            
            this.ID = Guid.NewGuid().ToString();
            this.ChunkNumber = chunkNumber;
            this.TotalChunks = totalChunks;
            this.Data = data;
            this.Timestamp = DateTime.Now;
        }
    }
}
