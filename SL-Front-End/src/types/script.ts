export interface Script {
  id: number;
  name: string;
  avgReturn: number;
  totalReturn: number;
  createDate: string;
  editDate: string;
}

export interface BuyCondition {
  id: string;
  expression: string;
}

export interface BuyConditionFormData {
  dataType: "daily" | "monthly";
  investmentAmount: number;
  startDate: string;
  endDate: string;
  commissionRate: number;
  conditions: BuyCondition[];
  logicExpression: string;
  priorityExpression: string;
  positionSizePercent: number;
  maxPositions: number;
  maxBuyPerStock: number;
  maxBuyPerStockEnabled: boolean;
  maxBuyPerDay: number;
  maxBuyPerDayEnabled: boolean;
  buyPriceBase: string;
  buyPriceAdjustment: number;
}

export interface SellConditionFormData {
  profitTargetEnabled: boolean;
  profitTargetPercent: number;
  stopLossEnabled: boolean;
  stopLossPercent: number;
  holdingPeriodEnabled: boolean;
  conditionalSellEnabled: boolean;
}

export interface TargetStock {
  id: number;
  name: string;
  selected: boolean;
}
