export type SyntheticRecord={id:string;name:string;version:string};
export type SyntheticRequest={id:string;name:string;version:string;requestId:string};
export type SyntheticResult={status:'applied';record:SyntheticRecord}|{status:'conflict';current:SyntheticRecord}|{status:'validation';fieldErrors:{name:string}}|{status:'unavailable';retryable:true}|{status:'not-found'|'request-id-conflict'};
export function createSyntheticTransport():{read(id:string):SyntheticRecord|null;save(input:SyntheticRequest):Promise<SyntheticResult>;failNext():void;trace():{requestId:string;id:string;status:SyntheticResult['status']}[]};
