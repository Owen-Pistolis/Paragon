namespace ParagonWebAPI.Types
{
    public class JsonFull
    {
        string ID { get; set; }
        string Data { get; set; }
        public JsonFull(string data) {

            this.ID = Guid.NewGuid().ToString();
            this.Data = data;
            
        }
    }
}
