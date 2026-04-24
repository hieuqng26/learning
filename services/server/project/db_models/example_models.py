from project import db
from .base_model import DBBaseModel


class IAMPathways(DBBaseModel):
    __tablename__ = 'iam_pathways'

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column('Model', db.String(255), nullable=False)
    scenario = db.Column('Scenario', db.String(255), nullable=False)
    identifier = db.Column('Identifier', db.String(16), nullable=False)
    region = db.Column('Region', db.String(255), nullable=True)
    variable = db.Column('Variable', db.String(255), nullable=True)
    unit = db.Column('Unit', db.String(255), nullable=True)
    year = db.Column('Year', db.Integer, nullable=True)
    value = db.Column('Value', db.Float, nullable=True)

    def to_dict(self):
        return {
            'Model': self.model,
            'Scenario': self.scenario,
            'Identifier': self.identifier,
            'Region': self.region,
            'Variable': self.variable,
            'Unit': self.unit,
            'Year': self.year,
            'Value': self.value
        }

    @staticmethod
    def transform_input(df):
        return df.melt(id_vars=['Model', 'Scenario', 'Identifier', 'Region', 'Variable', 'Unit'], var_name='Year', value_name='Value')

    @staticmethod
    def transform_output(df):
        return df.pivot_table(index=['Model', 'Scenario', 'Identifier', 'Region', 'Variable', 'Unit'], columns='Year', values='Value').reset_index()


class IAMBottomupPathways(DBBaseModel):
    __tablename__ = 'iam_bu_pathways'

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column('Model', db.String(255), nullable=False)
    scenario = db.Column('Scenario', db.String(255), nullable=False)
    region = db.Column('Region', db.String(255), nullable=True)
    variable = db.Column('Variable', db.String(255), nullable=True)
    unit = db.Column('Unit', db.String(255), nullable=True)
    year = db.Column('Year', db.Integer, nullable=True)
    value = db.Column('Value', db.Float, nullable=True)

    def to_dict(self):
        return {
            'Model': self.model,
            'Scenario': self.scenario,
            'Region': self.region,
            'Variable': self.variable,
            'Unit': self.unit,
            'Year': self.year,
            'Value': self.value
        }

    @staticmethod
    def transform_input(df):
        return df.melt(id_vars=['Model', 'Scenario', 'Region', 'Variable', 'Unit'], var_name='Year', value_name='Value')

    @staticmethod
    def transform_output(df):
        return df.pivot_table(index=['Model', 'Scenario', 'Region', 'Variable', 'Unit'], columns='Year', values='Value').reset_index()


class IAMMappingSector(DBBaseModel):
    __tablename__ = 'iam_mapping_sector'

    id = db.Column(db.Integer, primary_key=True)
    variable = db.Column('Variable', db.String(255), nullable=False)
    sector = db.Column('Sector', db.String(255), nullable=False)

    def to_dict(self):
        return {
            'Variable': self.variable,
            'Sector': self.sector
        }


class Intensities(DBBaseModel):
    __tablename__ = 'intensities'

    id = db.Column(db.Integer, primary_key=True)
    kbli_code = db.Column('KBLI Code', db.String(64), nullable=False)
    region = db.Column('region', db.String(8), nullable=False)
    s1 = db.Column('S1', db.Float, nullable=True)
    s2 = db.Column('S2', db.Float, nullable=True)
    revenue = db.Column('Revenue', db.Float, nullable=True)
    s1_intensity = db.Column('S1 Intensity', db.Float, nullable=True)
    s2_intensity = db.Column('S2 Intensity', db.Float, nullable=True)
    s3_upstream_intensity = db.Column('S3 Upstream Intensity', db.Float, nullable=True)
    s3_downstream_intensity = db.Column('S3 Downstream Intensity', db.Float, nullable=True)

    def to_dict(self):
        return {
            'KBLI Code': self.kbli_code,
            'region': self.region,
            'S1': self.s1,
            'S2': self.s2,
            'Revenue': self.revenue,
            'S1 Intensity': self.s1_intensity,
            'S2 Intensity': self.s2_intensity,
            'S3 Upstream Intensity': self.s3_upstream_intensity,
            'S3 Downstream Intensity': self.s3_downstream_intensity
        }


class PDCalibrate(DBBaseModel):
    __tablename__ = 'pd_calibrate'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column('Category', db.String(64), nullable=False)
    rating = db.Column('Rating', db.String(64), nullable=False)
    year = db.Column('Year', db.Integer, nullable=False)
    value = db.Column('Value', db.Float, nullable=True)

    def to_dict(self):
        return {
            'Category': self.category,
            'Rating': self.rating,
            'Year': self.year,
            'Value': self.value
        }

    @staticmethod
    def transform_input(df):
        return df.melt(id_vars=['Category', 'Rating'], var_name='Year', value_name='Value')

    @staticmethod
    def transform_output(df):
        return df.pivot_table(index=['Category', 'Rating'], columns='Year', values='Value').reset_index()


class Country(DBBaseModel):
    __tablename__ = 'country'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column('Code', db.String(16), nullable=False)
    country_name = db.Column('CountryName', db.Text(), nullable=False)

    def to_dict(self):
        return {
            'Code': self.code,
            'CountryName': self.country_name
        }


class Tax(DBBaseModel):
    __tablename__ = 'tax'

    id = db.Column(db.Integer, primary_key=True)
    country = db.Column('Country', db.String(64), nullable=False)
    continent = db.Column('Continent', db.String(64), nullable=False)
    corporate_tax_rate = db.Column('Corporate_Tax_Rate', db.Float, nullable=True)

    def to_dict(self):
        return {
            'Country': self.country,
            'Continent': self.continent,
            'Corporate_Tax_Rate': self.corporate_tax_rate
        }


class KBLICode(DBBaseModel):
    __tablename__ = 'kbli_code'

    id = db.Column(db.Integer, primary_key=True)
    kbli_code = db.Column('KBLI_Code', db.String(64), nullable=False)
    sector = db.Column('Sector', db.String(64), nullable=False)

    def to_dict(self):
        return {
            'KBLI_Code': self.kbli_code,
            'Sector': self.sector
        }


class SectorElasticity(DBBaseModel):
    __tablename__ = 'sector_elasticity'

    id = db.Column(db.Integer, primary_key=True)
    sector = db.Column('Sector', db.String(64), nullable=False)
    supply_elasticity = db.Column('Supply_Elasticity', db.Float, nullable=True)
    demand_elasticity = db.Column('Demand_Elasticity', db.Float, nullable=True)

    def to_dict(self):
        return {
            'Sector': self.sector,
            'Supply_Elasticity': self.supply_elasticity,
            'Demand_Elasticity': self.demand_elasticity
        }


class BottomupSectors(DBBaseModel):
    __tablename__ = 'bottomup_sectors'

    id = db.Column(db.Integer, primary_key=True)
    sektor = db.Column('Sektor', db.Text, nullable=False)
    sector = db.Column('Sector', db.Text, nullable=False)

    def to_dict(self):
        return {
            'Sektor': self.sektor,
            'Sector': self.sector
        }
