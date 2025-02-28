// Dummy Utils function

export const responseErrorObject = {
    data: {},
    status: 500,
    statusText: "",
    headers: {},
    config: {} 
}

export const isNull=(item: JSON)=>{
    if(item) return true;
    else return false;
}