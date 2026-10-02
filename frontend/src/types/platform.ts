export interface CatalogModel {
  id:string; name:string; module:string; type:string; algorithm:string|null; status:"ready"|"available"|"offline"|"unavailable"; version:string|null;
  trained_at:string|null; dataset:string|null; metric_name:string|null; metric_value:number|null; detail_path:string;
}
export interface CatalogDataset {
  id:string; name:string; module:string; kind:"tabular"|"temporal"|"text"; records:number; related_records:number|null;
  columns:string[]; column_count:number; created_at:string|null; seed:number|null; synthetic:boolean; formats:string[];
  download_urls:Record<string,string>; view_path:string; import_path:string; explore_path:string; can_regenerate:boolean;
}
export interface DatasetDetail extends CatalogDataset {
  preview:Record<string,unknown>[]; missing_values:Record<string,number>; missing_total:number;
  statistics:Record<string,{mean:number;minimum:number|null;maximum:number|null}>;
  distribution?:Record<string,number>; time_range?:{first:string|null;last:string|null}; average_text_length?:number; terms?:{term:string;count:number}[];
}
export interface AnalysisHistory {
  id:string; module:string; analysis_type:string; model_name:string; model_version:string|null; record_reference:string|null;
  result_summary:string; created_at:string; source_history_id:string|null;
}
export interface HistoryPage { items:AnalysisHistory[]; total:number; page:number; page_size:number }
export interface SystemStatus { backend:string; database:string; datasets:{status:string;count:number};models:{status:string;count:number};llm:{provider:string;available:boolean;model:string|null;mode:string};vision:{status:string;description:string} }
