/****** Object:  Table [dbo].[Plans]    Script Date: 2024-06-25 12:28:26 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Plans](
	[planID] [int] IDENTITY(1,1) NOT NULL,
	[custType] [int] NOT NULL,
	[name] [varchar](max) NOT NULL,
	[amount] [money] NOT NULL,
	[priceID] [varchar](max) NULL,
	[productID] [varchar](max) NULL,
	[description] [varchar](max) NULL,
	[interval] [varchar](10) NOT NULL,
	[trialDays] [int] NULL,
	[created] [datetime] NOT NULL,
	[active] [int] NOT NULL,
	[planHistoryNum] [int] NOT NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

