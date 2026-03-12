export interface Job {
    title: string,
    category: string,
    numOpenings: number;
    description: string,
    responsibilities: Array<string>,
    preferredSkills: Array<string>,
    otherAttributes: Array<string>,
    compensation: string
}