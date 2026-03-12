namespace ParagonWebAPI.Types
{
    public class Action
    {
        string actionID { get; set; }
        string previousActionID {  get; set; }
        string nextActionID { get; set; }
        string ActionName { get; set; }

        Action nextAction { get; set; }
        Action previousAtion { get; set; }

        public Action() { }
    }
}
